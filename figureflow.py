"""Local figure audit tools and optional design-explicit scientific analysis.

Never infers experimental design or edits native projects. Analyze requires [science].
Optional AI: start with ai-setup and ai-doctor; ordinary commands stay offline.
"""
import argparse
import csv
import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from figureflow_lint import lint_manifest, list_rules

__version__ = '0.5.0'


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def load_json(path):
    def invalid(value):
        raise ValueError('Non-finite JSON number: ' + value)
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON key: ' + key)
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding='utf-8-sig'), parse_constant=invalid,
                      object_pairs_hook=unique)


def number(value):
    if isinstance(value, bool) or value is None:
        raise ValueError('Expected a finite number')
    try:
        result = Decimal(str(value))
    except InvalidOperation as e:
        raise ValueError('Invalid number: ' + str(value)) from e
    if not result.is_finite():
        raise ValueError('Non-finite number')
    return result


KEY = ('panel', 'condition', 'group', 'observation_id')
REQUIRED = set(KEY) | {'sample_id', 'value', 'unit'}


def observations(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        if len(fields) != len(set(fields)) or not REQUIRED.issubset(fields):
            raise ValueError('CSV needs unique columns: ' + ', '.join(sorted(REQUIRED)))
        rows = {}
        for row in reader:
            if None in row or any(v is None for v in row.values()):
                raise ValueError('Malformed CSV row at line ' + str(reader.line_num))
            if any(not row[k].strip() for k in REQUIRED - {'value'}):
                raise ValueError('Missing identity/unit at line ' + str(reader.line_num))
            key = tuple(row[k] for k in KEY)
            if key in rows:
                raise ValueError('Duplicate observation identity: ' + repr(key))
            if row['value'] != '':
                number(row['value'])
            rows[key] = row
    if not rows:
        raise ValueError('Empty observation table')
    return fields, rows


def counts(rows):
    groups = defaultdict(list)
    for key, row in rows.items():
        groups[key[:3]].append(row)
    result = []
    for key, items in sorted(groups.items()):
        nonmissing = [r for r in items if r['value'] != '']
        result.append(dict(zip(KEY[:3], key), n_observations=len(nonmissing),
                           n_unique_samples=len({r['sample_id'] for r in nonmissing}),
                           missing=len(items) - len(nonmissing)))
    return result


def audit(source, candidate, exclusions=None):
    sf, sr = observations(source)
    cf, cr = observations(candidate)
    errors, removed = [], set()
    if set(sf) != set(cf):
        errors.append({'type': 'columns_changed', 'source': sf, 'candidate': cf})
    for entry in exclusions or []:
        key = tuple(entry[k] for k in KEY)
        if key in removed or key not in sr:
            raise ValueError('Unknown or duplicate exclusion: ' + repr(key))
        if not entry.get('reason', '').strip() or not entry.get('authorization', '').strip():
            raise ValueError('Exclusions require reason and authorization reference')
        if entry['expected_value'] != sr[key]['value']:
            raise ValueError('Exclusion source value changed')
        removed.add(key)
    expected = {k: v for k, v in sr.items() if k not in removed}
    for key in sorted(set(expected) - set(cr)):
        errors.append({'type': 'missing_observation', 'key': key})
    for key in sorted(set(cr) - set(expected)):
        errors.append({'type': 'unexpected_observation', 'key': key})
    for key in sorted(set(expected) & set(cr)):
        for field in sorted(set(sf) & set(cf)):
            a, b = expected[key][field], cr[key][field]
            equal = (number(a) == number(b)) if field == 'value' and a != '' and b != '' else a == b
            if not equal:
                errors.append({'type': 'changed', 'key': key, 'field': field, 'source': a, 'candidate': b})
    return {'status': 'fail' if errors else 'pass', 'errors': errors,
            'source_sha256': sha256(source), 'candidate_sha256': sha256(candidate),
            'authorized_exclusions': exclusions or [], 'source_counts': counts(sr),
            'candidate_counts': counts(cr),
            'scope': 'CSV fidelity only; counts do not establish biological independence'}


def stars(p):
    p = number(p)
    if not 0 <= p <= 1:
        raise ValueError('P must lie in [0, 1]')
    for threshold, label in [('0.0001', '****'), ('0.001', '***'), ('0.01', '**'), ('0.05', '*')]:
        if p <= Decimal(threshold):
            return label
    return 'ns'


def annotation_plan(data):
    order = data['group_order']
    if not isinstance(order, list) or not order or any(not isinstance(x, str) or not x for x in order) or len(order) != len(set(order)):
        raise ValueError('group_order must contain distinct, nonempty names')
    if not isinstance(data['comparisons'], list) or not data['comparisons']:
        raise ValueError('comparisons must be a nonempty list (all may be nonsignificant)')
    positions = {name: i for i, name in enumerate(order)}
    buckets, seen, comparisons = defaultdict(list), set(), []
    for original in data['comparisons']:
        c = dict(original)
        for field in ('panel', 'condition', 'reference', 'target', 'test', 'correction', 'family'):
            if not isinstance(c.get(field), str) or not c[field].strip():
                raise ValueError('Comparison missing ' + field)
        if c['reference'] not in positions or c['target'] not in positions or c['reference'] == c['target']:
            raise ValueError('Unknown group or self-comparison')
        identity = (c['panel'], c['condition'], c['test'], c['correction'], c['family'],
                    tuple(sorted([c['reference'], c['target']])))
        if identity in seen:
            raise ValueError('Duplicate comparison in the same family')
        seen.add(identity)
        c['stars'] = stars(c['p_adjusted'])
        comparisons.append(c)
        if c['stars'] != 'ns':
            key = tuple(c[f] for f in ('panel', 'condition', 'reference', 'test', 'correction', 'family'))
            buckets[key].append(c)
    annotations = []
    for key, cs in buckets.items():
        runs = []
        for c in sorted(cs, key=lambda c: positions[c['target']]):
            if not runs or positions[c['target']] != positions[runs[-1][-1]['target']] + 1:
                runs.append([])
            runs[-1].append(c)
        for run in runs:
            worst = max(number(c['p_adjusted']) for c in run)
            annotations.append(dict(zip(('panel', 'condition', 'reference', 'test', 'correction', 'family'), key),
                                    targets=[c['target'] for c in run], stars=stars(worst),
                                    maximum_adjusted_p=str(worst), comparisons=run))
    return {'status': 'pass', 'calculates_p_values': False, 'comparisons': comparisons,
            'annotations': annotations, 'font': 'Arial', 'bold': True, 'font_size_pt': 10,
            'scope': 'Plan from supplied adjusted P values; scientific/model validation remains separate'}


def layout_audit(data):
    tolerance = number(data['tolerance_pt'])
    if tolerance < 0:
        raise ValueError('Negative tolerance')
    panels = data['panels']
    if not isinstance(panels, list) or not panels or len({p['id'] for p in panels}) != len(panels):
        raise ValueError('Panels must have unique IDs and not be empty')
    for p in panels:
        if not {'id','row','column','baseline_pt','x_origin_pt','label_top_pt','grid_required'}.issubset(p):
            raise ValueError('Missing panel measurement fields; use explicit null for absent labels/columns')
        if type(p['grid_required']) is not bool:
            raise ValueError('grid_required must be a JSON boolean')
        if p['row'] is None:
            raise ValueError('Every panel needs a row alignment group')
    errors = []
    for bucket_field, coordinate in [('row', 'baseline_pt'), ('row', 'label_top_pt'), ('column', 'x_origin_pt')]:
        buckets = defaultdict(list)
        for panel in panels:
            if panel.get(bucket_field) is not None and panel.get(coordinate) is not None:
                buckets[str(panel[bucket_field])].append((panel['id'], number(panel[coordinate])))
        for bucket, values in buckets.items():
            spread = max(v for _, v in values) - min(v for _, v in values)
            if spread > tolerance:
                errors.append({'type': 'not_collinear', 'coordinate': coordinate, 'bucket': bucket,
                               'panels': [p for p, _ in values], 'spread_pt': str(spread)})
    for panel in panels:
        for field in ('baseline_pt', 'x_origin_pt'):
            number(panel[field])
        if panel.get('grid_required', False):
            step = number(data['grid_pt'])
            if step <= 0:
                raise ValueError('Grid spacing must be positive')
            for field in ('baseline_pt', 'x_origin_pt'):
                value = number(panel[field])
                delta = abs(value - (value / step).to_integral_value() * step)
                if delta > tolerance:
                    errors.append({'type': 'off_grid', 'panel': panel['id'], 'coordinate': field, 'delta_pt': str(delta)})
        for measured, target in [('legend_gap_pt', 'expected_legend_gap_pt'), ('legend_bottom_gap_pt', 'expected_legend_bottom_gap_pt')]:
            if target in panel:
                delta = abs(number(panel[measured]) - number(panel[target]))
                if delta > tolerance:
                    errors.append({'type': 'legend_gap', 'panel': panel['id'], 'coordinate': measured, 'delta_pt': str(delta)})
    return {'status': 'fail' if errors else 'pass', 'errors': errors,
            'scope': 'Supplied measurements only; no automatic axis detection or visual inspection'}


def verify_evidence(data, root):
    root = Path(root).resolve()
    required = data['required_checks']
    if not isinstance(required, list) or not required or any(not isinstance(k,str) or not k for k in required) or len(required) != len(set(required)):
        raise ValueError('required_checks must be nonempty and unique')
    checks = {c['id']: c for c in data['checks']}
    if len(checks) != len(data['checks']):
        raise ValueError('Duplicate check ID')
    errors = []
    for key in required:
        c = checks.get(key)
        if not c:
            errors.append({'id': key, 'error': 'missing check'})
            continue
        if c.get('status') not in ('pass', 'not_applicable'):
            errors.append({'id': key, 'error': 'unresolved or failed'})
            continue
        if not c.get('reviewer') or not c.get('reason'):
            errors.append({'id': key, 'error': 'missing reviewer/reason'})
        try:
            if not isinstance(c.get('checked_at'), str):
                raise ValueError('checked_at must be a timestamp string')
            stamp = datetime.fromisoformat(c['checked_at'].replace('Z', '+00:00'))
            if stamp.tzinfo is None or stamp > datetime.now(timezone.utc):
                raise ValueError('Invalid audit time')
        except (KeyError, ValueError, TypeError):
            errors.append({'id': key, 'error': 'missing/invalid timezone-aware checked_at'})
        artifacts = c.get('artifacts', [])
        if not artifacts:
            errors.append({'id': key, 'error': 'missing evidence artifact (including N/A justification)'})
        for artifact in artifacts:
            path = (root / artifact['path']).resolve()
            if not path.is_relative_to(root) or not path.is_file():
                errors.append({'id': key, 'error': 'missing or out-of-workspace artifact'})
            elif sha256(path) != artifact['sha256']:
                errors.append({'id': key, 'error': 'stale artifact', 'path': artifact['path']})
    return {'status': 'fail' if errors else 'pass', 'errors': errors,
            'scope': 'Evidence completeness and hashes; does not independently prove reviewer judgments'}


def prism_export_script(data, output_dir):
    directory = Path(output_dir).resolve()
    if any(c in str(directory) for c in '\n\r"'):
        raise ValueError('Unsafe export path')
    lines, ids, pages = [], set(), set()
    for p in data['panels']:
        if p['section'] not in ('G', 'L') or type(p['page']) is not int or p['page'] < 1:
            raise ValueError('Invalid Prism section/page')
        name = p['id']
        if not name or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in name):
            raise ValueError('Panel ID must be a safe filename')
        page = (p['section'], p['page'])
        if name in ids or page in pages:
            raise ValueError('Duplicate panel/page mapping')
        ids.add(name)
        pages.add(page)
        target = directory / (name + '.pdf')
        if target.exists():
            raise ValueError('Export target already exists: ' + str(target))
        lines.extend([f"GoTo {p['section']}, {p['page']}", f'ExportPDF "{target}"'])
    if not lines:
        raise ValueError('Empty export plan')
    lines.append('CloseScriptDialog')
    return '\n'.join(lines) + '\n'


def summarize_reports(paths):
    """Aggregate declared check outcomes without rerunning or endorsing their evidence."""
    reports = []
    seen = set()
    for path in paths:
        resolved = Path(path).resolve()
        if resolved in seen:
            raise ValueError('Duplicate report path')
        seen.add(resolved)
        report = load_json(resolved)
        if not isinstance(report, dict) or type(report.get('report_version')) is not int or report['report_version'] != 1:
            raise ValueError('Expected a version 1 figureflow report')
        if report.get('command') not in ('audit', 'plan', 'layout', 'verify', 'lint', 'analyze') or report.get('status') not in ('pass', 'fail'):
            raise ValueError('Expected a supported check report with pass/fail status')
        if not isinstance(report.get('tool_version'), str) or not report['tool_version']:
            raise ValueError('Report missing tool version')
        reports.append({'file': resolved.name, 'sha256': sha256(resolved),
                        'command': report['command'], 'status': report['status'],
                        'tool_version': report['tool_version'],
                        'full_rule_set': report.get('full_rule_set'),
                        'scope': report.get('scope', 'Unspecified; inspect original report')})
    if not reports:
        raise ValueError('Provide at least one report')
    return {'status': 'fail' if any(r['status'] == 'fail' for r in reports) else 'pass',
            'reports': reports, 'report_count': len(reports), 'complete_figure_acceptance': False,
            'scope': 'Supplied reports only; does not rerun checks, establish freshness, or replace final evidence review'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--version', action='version', version='figureflow ' + __version__)
    subs = parser.add_subparsers(dest='command', required=True)
    p = subs.add_parser('ai-setup', help='Recommended first step: create optional API config, without storing a key')
    p.add_argument('--config', default='local/ai-config.json'); p.add_argument('--model', required=True)
    p.add_argument('--base-url', default='https://api.openai.com/v1')
    p.add_argument('--protocol', choices=('responses','chat_completions'), default='responses')
    p.add_argument('--api-key-env', default='FIGUREFLOW_API_KEY')
    p.add_argument('--chat-token-parameter', choices=('max_completion_tokens','max_tokens'), default='max_completion_tokens')
    p = subs.add_parser('ai-doctor', help='Check API config and key presence locally; no network')
    p.add_argument('--config', default='local/ai-config.json')
    p = subs.add_parser('ai-prepare', help='Prepare a reviewable API request without sending it')
    p.add_argument('--config', default='local/ai-config.json'); p.add_argument('--problem', required=True)
    p.add_argument('--context', help='Optional reviewed plain-text summary; never attaches other files')
    p = subs.add_parser('ai-ask', help='Preview a prepared request; --send authorizes one API call')
    p.add_argument('input'); p.add_argument('--config', default='local/ai-config.json'); p.add_argument('--send', action='store_true')
    p = subs.add_parser('inspect', help='Inspect CSV/TSV/XLSX without inferring design')
    p.add_argument('input'); p.add_argument('--sheet')
    p = subs.add_parser('analyze', help='Run an explicit analysis and render SVG/PDF/PNG')
    p.add_argument('input'); p.add_argument('--output-dir', required=True)
    p.add_argument('--ai-help', action='store_true', help='On failure, send one fixed error-category summary to the configured API; preserves failure status')
    p.add_argument('--ai-config', default='local/ai-config.json')
    p = subs.add_parser('audit', help='Compare source and candidate observations exactly')
    p.add_argument('source'); p.add_argument('candidate'); p.add_argument('--exclusions')
    p = subs.add_parser('plan'); p.add_argument('input')
    p = subs.add_parser('layout'); p.add_argument('input')
    p = subs.add_parser('verify'); p.add_argument('input'); p.add_argument('--root', required=True)
    p = subs.add_parser('prism-export'); p.add_argument('input'); p.add_argument('--directory', required=True)
    p = subs.add_parser('hash'); p.add_argument('input')
    p = subs.add_parser('lint', help='Check declared figure formatting with numbered rules')
    p.add_argument('input')
    p.add_argument('--profile', default='uwm', help='uwm (legacy), generic, or strict profile JSON path')
    p.add_argument('--select', help='Comma-separated exact rule codes; omitted means all rules')
    p.add_argument('--format', choices=('json', 'text'), default='json')
    p = subs.add_parser('rules', help='List supported checks and their meanings')
    p = subs.add_parser('summary', help='Aggregate existing check reports without re-running analyses')
    p.add_argument('inputs', nargs='+')
    for p in subs.choices.values():
        p.allow_abbrev = False
        p.add_argument('--out', help='Create a new output file; refuses to overwrite')
        p.add_argument('--error-format', choices=('text', 'json'), default='text',
                       help='Format runtime input/file errors on stderr (usage errors remain text)')
    args = parser.parse_args(argv)
    analysis_started = False
    try:
        if args.out and Path(args.out).exists():
            raise ValueError('Output report already exists; choose a new file')
        if args.command.startswith('ai-'):
            import figureflow_ai as ai
            if args.command == 'ai-setup':
                result = ai.setup(args.config,args.model,args.base_url,args.protocol,args.api_key_env,args.chat_token_parameter)
            elif args.command == 'ai-doctor': result = ai.doctor(args.config)
            elif args.command == 'ai-prepare':
                context = None
                if args.context:
                    if Path(args.context).stat().st_size > ai.MAX_INPUT*4:
                        raise ValueError('Context file too large; provide a short reviewed summary')
                    context = Path(args.context).read_text(encoding='utf-8')
                result = ai.prepare(ai.load_config(args.config),args.problem,context)
            else: result = ai.ask(args.config,load_json(args.input),args.send)
        elif args.command == 'inspect':
            from figureflow_science import inspect_table
            result = inspect_table(args.input, args.sheet)
        elif args.command == 'analyze':
            from figureflow_science import analyze
            analysis_started = True
            result = analyze(args.input, args.output_dir)
        elif args.command == 'audit':
            result = audit(args.source, args.candidate, load_json(args.exclusions) if args.exclusions else [])
        elif args.command == 'plan': result = annotation_plan(load_json(args.input))
        elif args.command == 'layout': result = layout_audit(load_json(args.input))
        elif args.command == 'verify': result = verify_evidence(load_json(args.input), args.root)
        elif args.command == 'prism-export': result = prism_export_script(load_json(args.input), args.directory)
        elif args.command == 'lint':
            result = lint_manifest(load_json(args.input), args.select.split(',') if args.select is not None else None,
                                   args.profile if args.profile in ('uwm', 'generic') else load_json(args.profile))
        elif args.command == 'rules': result = list_rules()
        elif args.command == 'summary': result = summarize_reports(args.inputs)
        else: result = {'status': 'pass', 'sha256': sha256(args.input)}
        if isinstance(result, dict):
            result.update(report_version=1, tool_version=__version__, command=args.command)
        if isinstance(result, dict) and args.command in ('plan', 'layout', 'verify', 'lint'):
            result['input_sha256'] = sha256(args.input)
        text = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
        if args.command == 'lint' and args.format == 'text':
            lines = [f"{d['path']}: {d['code']} {d['message']}" for d in result['diagnostics']]
            lines.append(f"{result['status']}: {len(result['diagnostics'])} errors; "
                         f"{len(result['selected_rules'])} selected rules; {result['panel_count']} panels")
            lines.append(result['scope'])
            text = '\n'.join(lines) + '\n'
        if args.out:
            with Path(args.out).open('x', encoding='utf-8') as f: f.write(text)
        else: print(text, end='')
        return 1 if isinstance(result, dict) and result.get('status') == 'fail' else 0
    except (ValueError, OSError, KeyError, TypeError, AttributeError, csv.Error) as e:
        error = {'status':'error','code':'INPUT001','message':str(e),
                 'report_version':1,'tool_version':__version__,'command':args.command}
        if args.command == 'analyze':
            error['help_hint'] = 'Recommended: configure optional AI with ai-setup, check ai-doctor, then use ai-prepare/ai-ask or --ai-help. See AI_API.md.'
            if args.ai_help and analysis_started:
                try:
                    from figureflow_ai import failure_request, ask
                    request = failure_request(args.ai_config,e)
                    error['ai_advice'] = ask(args.ai_config,request,send=True)
                except (ValueError,OSError,TypeError,KeyError) as ai_error:
                    error['ai_assistance_error'] = str(ai_error)
        if args.error_format == 'json':
            print(json.dumps(error,ensure_ascii=False),file=sys.stderr)
        else:
            print('figureflow: '+str(e),file=sys.stderr)
            if 'help_hint' in error: print(error['help_hint'],file=sys.stderr)
            if 'ai_advice' in error: print(json.dumps(error['ai_advice'],ensure_ascii=False,indent=2),file=sys.stderr)
            if 'ai_assistance_error' in error: print('AI assistance: '+error['ai_assistance_error'],file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
