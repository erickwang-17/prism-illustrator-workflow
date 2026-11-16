"""Offline API contract tests: synthetic credentials, mocked transport, no billed calls."""
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock
from urllib.error import HTTPError, URLError

import figureflow as cli
import figureflow_ai as ai


class AITests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.path=self.root/'api.json'
        ai.setup(self.path,'synthetic-model')
        self.config=ai.load_config(self.path)
        self.env=patch.dict(os.environ,{'FIGUREFLOW_API_KEY':'synthetic-secret-123'},clear=True)
        self.env.start();self.addCleanup(self.env.stop);self.addCleanup(self.temp.cleanup)

    def response(self,text='Review the paired IDs first.'):
        return {'status':'completed','output':[{'type':'reasoning','summary':[]},
            {'type':'message','content':[{'type':'output_text','text':text}]}],
            'usage':{'input_tokens':90,'output_tokens':24,'total_tokens':114,'secret':'not copied'}}

    def test_setup_does_not_store_credentials_or_overwrite(self):
        self.assertNotIn('synthetic-secret',self.path.read_text())
        with self.assertRaises(FileExistsError):ai.setup(self.path,'other-model')

    def test_doctor_is_offline_and_does_not_echo_key(self):
        with patch.object(ai,'http_post') as transport:
            report=ai.doctor(self.path);transport.assert_not_called()
        self.assertEqual(report['status'],'pass');self.assertFalse(report['live_api_verified'])
        self.assertNotIn('synthetic-secret',json.dumps(report))
        with patch.dict(os.environ,{},clear=True):self.assertEqual(ai.doctor(self.path)['status'],'fail')

    def test_config_rejects_secrets_unknown_fields_and_unsafe_urls(self):
        for url in ['http://example.test/v1','https://key@example.test/v1','https://example.test/v1?key=secret',
                    'https://example.test/#token','https://example.test/../v1','https://example.test/%2e%2e/v1']:
            c=dict(self.config,base_url=url)
            with self.subTest(url=url),self.assertRaises(ai.AIError):ai.validate_config(c)
        with self.assertRaises(ai.AIError):ai.validate_config(dict(self.config,api_key='do-not-store'))
        for field,value in [('timeout_seconds',True),('max_output_tokens',999999),('model',''),('api_key_env','secret-value')]:
            with self.subTest(field=field),self.assertRaises(ai.AIError):ai.validate_config(dict(self.config,**{field:value}))

    def test_prepare_does_not_call_network_and_redacts_known_key(self):
        with patch.object(ai,'http_post') as transport:
            request=ai.prepare(self.config,'Failure synthetic-secret-123', 'Bearer abcdef012345; sk-testsecret123')
            transport.assert_not_called()
        self.assertNotIn('synthetic-secret-123',json.dumps(request))
        self.assertNotIn('sk-testsecret123',json.dumps(request))
        self.assertFalse(request['body']['store'])
        self.assertEqual(request['body']['max_output_tokens'],2048)

    def test_preview_does_not_require_key(self):
        request=ai.prepare(self.config,'How to diagnose unmatched pairs?')
        with patch.dict(os.environ,{},clear=True),patch.object(ai,'http_post') as transport:
            result=ai.ask(self.path,request);transport.assert_not_called()
            self.assertEqual(result['status'],'preview')
            with self.assertRaisesRegex(ai.AIError,'key is not set'):ai.ask(self.path,request,send=True)

    def test_one_responses_call_is_advisory_and_reports_usage(self):
        request=ai.prepare(self.config,'Explain missing pairs.')
        with patch.object(ai,'http_post',return_value=self.response('No edits. synthetic-secret-123')) as transport:
            result=ai.ask(self.path,request,send=True)
            transport.assert_called_once()
            self.assertEqual(transport.call_args.args[0],'https://api.openai.com/v1/responses')
        self.assertEqual(result['status'],'advisory');self.assertFalse(result['actions_executed'])
        self.assertTrue(result['review_required']);self.assertEqual(result['usage']['total_tokens'],114)
        self.assertNotIn('synthetic-secret-123',json.dumps(result));self.assertNotIn('secret',result['usage'])

    def test_custom_chat_endpoint_and_both_token_limit_parameters(self):
        for parameter in ('max_completion_tokens','max_tokens'):
            c=dict(self.config,protocol='chat_completions',base_url='https://provider.example/v1',chat_token_parameter=parameter)
            self.path.write_text(json.dumps(c));request=ai.prepare(c,'Synthetic question')
            self.assertEqual(request['endpoint'],'https://provider.example/v1/chat/completions')
            self.assertEqual(request['body'][parameter],2048)
            response={'choices':[{'finish_reason':'stop','message':{'content':'Check units.'}}],'usage':{'completion_tokens':3}}
            with patch.object(ai,'http_post',return_value=response):result=ai.ask(self.path,request,send=True)
            self.assertEqual(result['advice'],'Check units.')

    def test_config_and_payload_tampering_block_network(self):
        request=ai.prepare(self.config,'Question')
        for mutate in [lambda r:r.update(endpoint='https://evil.example'),
                       lambda r:r['body'].update(tools=[{'type':'shell'}]),
                       lambda r:r['body'].update(model='other'),
                       lambda r:r.update(config_fingerprint='changed')]:
            changed=copy.deepcopy(request);mutate(changed)
            with patch.object(ai,'http_post') as transport,self.assertRaises(ai.AIError):
                try:ai.ask(self.path,changed,send=True)
                finally:transport.assert_not_called()

    def test_oversized_input_rejected(self):
        with self.assertRaisesRegex(ai.AIError,'16000'):ai.prepare(self.config,'x'*ai.MAX_INPUT)

    def test_refusal_empty_and_tool_only_responses_rejected(self):
        c=dict(self.config,protocol='chat_completions')
        for response in [{'choices':[]},{'choices':[{'finish_reason':'tool_calls','message':{'tool_calls':[{}]}}]},
                         {'choices':[{'finish_reason':'stop','message':{'content':None,'refusal':'No'}}]}]:
            with self.assertRaises(ai.AIError):ai.parse_response(c,response)
        for response in [{'status':'failed','error':{'message':'private'}},
                         {'status':'completed','output':[{'type':'function_call','name':'shell'}]},
                         {'status':'completed','output':[{'type':'message','content':[{'type':'refusal','refusal':'No'}]}]}]:
            with self.assertRaises(ai.AIError):ai.parse_response(self.config,response)

    def test_truncation_is_not_claimed_as_complete_advice(self):
        response=self.response('Partial proposal');response['status']='incomplete'
        self.assertTrue(ai.parse_response(self.config,response)[1])

    def test_http_transport_headers_timeout_and_json_body(self):
        context=Mock();context.__enter__=Mock(return_value=context);context.__exit__=Mock(return_value=False)
        context.read.return_value=json.dumps(self.response()).encode()
        opener=Mock();opener.open.return_value=context
        with patch.object(ai,'build_opener',return_value=opener):
            result=ai.http_post('https://example.test/v1/responses',{'model':'test'},'test-only-key',12)
        request=opener.open.call_args.args[0]
        self.assertEqual(request.get_method(),'POST');self.assertEqual(request.get_header('Authorization'),'Bearer test-only-key')
        self.assertEqual(json.loads(request.data),{'model':'test'})
        self.assertEqual(opener.open.call_args.kwargs['timeout'],12)
        self.assertEqual(context.read.call_args.args[0],ai.MAX_RESPONSE+1)
        self.assertEqual(result['status'],'completed')

    def test_errors_are_sanitized_no_retry_no_redirect(self):
        for error in [HTTPError('https://example.test',401,'synthetic-secret-123',{},io.BytesIO(b'private')),
                      HTTPError('https://example.test',429,'private',{},io.BytesIO(b'private')),
                      URLError('synthetic-secret-123'),TimeoutError('synthetic-secret-123')]:
            opener=Mock();opener.open.side_effect=error
            with patch.object(ai,'build_opener',return_value=opener),self.assertRaises(ai.AIError) as raised:
                ai.http_post('https://example.test',{},'test-only-key',1)
            self.assertNotIn('synthetic-secret',str(raised.exception));opener.open.assert_called_once()
        self.assertIsNone(ai.NoRedirect().redirect_request(None,None,302,'redirect',{},'https://evil.example'))

    def test_malformed_or_oversized_http_response_rejected(self):
        for raw in [b'not json',b'[]',b'x'*(ai.MAX_RESPONSE+1)]:
            context=Mock();context.__enter__=Mock(return_value=context);context.__exit__=Mock(return_value=False);context.read.return_value=raw
            opener=Mock();opener.open.return_value=context
            with patch.object(ai,'build_opener',return_value=opener),self.assertRaises(ai.AIError):
                ai.http_post('https://example.test',{},'test-only-key',1)

    def test_automatic_failure_context_excludes_values_and_paths(self):
        request=ai.failure_request(self.path,ValueError('Missing cells at /private/subject-123.csv row 15: patient_name'))
        content=json.dumps(request)
        self.assertNotIn('/private',content);self.assertNotIn('subject-123',content);self.assertNotIn('patient_name',content)
        self.assertIn('missing observations',content)

    def test_ai_help_keeps_analysis_error_and_no_output(self):
        settings=self.root/'bad.json';settings.write_text('{}');out=self.root/'output'
        stdout,stderr=io.StringIO(),io.StringIO()
        with patch('figureflow_science.analyze',side_effect=ValueError('Missing cells at source row 4')),patch.object(ai,'http_post',return_value=self.response()) as transport,contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
            code=cli.main(['analyze',str(settings),'--output-dir',str(out),'--ai-help','--ai-config',str(self.path),'--error-format','json'])
        self.assertEqual(code,2);self.assertEqual(stdout.getvalue(),'');self.assertFalse(out.exists())
        result=json.loads(stderr.getvalue());self.assertEqual(result['status'],'error');self.assertEqual(result['ai_advice']['status'],'advisory')
        transport.assert_called_once()

    def test_offline_error_only_recommends_setup(self):
        settings=self.root/'bad.json';settings.write_text('{}')
        stderr=io.StringIO()
        with patch('figureflow_science.analyze',side_effect=ValueError('Missing cells at source row 4')),patch.object(ai,'http_post') as transport,contextlib.redirect_stderr(stderr):
            code=cli.main(['analyze',str(settings),'--output-dir',str(self.root/'output'),'--error-format','json'])
        self.assertEqual(code,2);transport.assert_not_called();self.assertIn('ai-setup',stderr.getvalue())

    def test_cli_preexisting_report_does_not_spend_api_call(self):
        request=self.root/'request.json';request.write_text(json.dumps(ai.prepare(self.config,'Question')))
        out=self.root/'exists.json';out.write_text('keep')
        with patch.object(ai,'http_post') as transport,contextlib.redirect_stderr(io.StringIO()):
            code=cli.main(['ai-ask',str(request),'--config',str(self.path),'--send','--out',str(out)])
        self.assertEqual(code,2);transport.assert_not_called();self.assertEqual(out.read_text(),'keep')

    def test_ai_advice_cannot_count_as_a_verified_analysis_report(self):
        report=self.root/'advice.json'
        report.write_text(json.dumps(dict(report_version=1,tool_version='0.4.0',command='ai-ask',status='advisory')))
        with self.assertRaises(ValueError):cli.summarize_reports([report])

    def test_ai_failure_does_not_mask_original_analysis_error(self):
        stderr=io.StringIO()
        with patch('figureflow_science.analyze',side_effect=ValueError('Incomplete pairs')),patch.object(ai,'http_post',side_effect=ai.AIError('API HTTP 429')),contextlib.redirect_stderr(stderr):
            code=cli.main(['analyze','not-read.json','--output-dir',str(self.root/'out'),'--ai-help','--ai-config',str(self.path),'--error-format','json'])
        report=json.loads(stderr.getvalue());self.assertEqual(code,2)
        self.assertEqual(report['message'],'Incomplete pairs');self.assertIn('429',report['ai_assistance_error'])

    def test_success_does_not_invoke_optional_failure_api(self):
        with patch('figureflow_science.analyze',return_value={'status':'pass'}),patch.object(ai,'http_post') as transport,contextlib.redirect_stdout(io.StringIO()):
            code=cli.main(['analyze','not-read.json','--output-dir',str(self.root/'out'),'--ai-help'])
        self.assertEqual(code,0);transport.assert_not_called()


if __name__=='__main__':unittest.main()
