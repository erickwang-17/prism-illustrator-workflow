"""Explicit figure-manifest checks; never edits or introspects native projects."""
import re


RULES = {
    'NAM001': ('canonical-control', 'Use Vav-Cre for the control legend name.'),
    'LEG001': ('sample-count', 'Each legend needs one positive (n=N), matching audited_n.'),
    'LEG002': ('sample-italics', 'Render the sample-count suffix in italics.'),
    'LEG003': ('legend-order', 'Legend group IDs must follow the declared group_order.'),
    'FMT001': ('arial', 'All reported text must use Arial.'),
    'FMT002': ('native-symbol-border', 'Scatter symbols must be native circles with black borders.'),
    'FMT003': ('error-bars', 'Scatter error bars must be black, above symbols, and match the reference width.'),
    'FMT004': ('axes', 'Axis labels/titles must be bold; remove scatter x ticks and XTitle.'),
    'STA001': ('star-format', 'Reported stars must be Arial, bold, 10 pt, and contain 1–4 stars or ns.'),
    'COL001': ('exact-fill', 'Each symbol fill must equal its declared reference RGB hex value.'),
}

# Bounded, anchored patterns; no user-supplied regex or automatic substitution.
SAMPLE_RE = re.compile(r'\(n=([1-9][0-9]*)\)\Z', re.ASCII)
HEX_RE = re.compile(r'#[0-9A-Fa-f]{6}\Z', re.ASCII)
ID_RE = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z', re.ASCII)
STAR_RE = re.compile(r'(?:\*{1,4}|ns)\Z', re.ASCII)


def object_fields(value, fields, path):
    if not isinstance(value, dict):
        raise ValueError(f'{path}: expected an object')
    missing, unknown = fields - value.keys(), value.keys() - fields
    if missing or unknown:
        raise ValueError(f'{path}: missing={sorted(missing)}, unknown={sorted(unknown)}')


def text(value, path):
    if not isinstance(value, str) or not value.strip() or len(value) > 256:
        raise ValueError(f'{path}: expected nonempty text of at most 256 characters')


def positive(value, path):
    if type(value) not in (int, float) or not 0 < value < float('inf'):
        raise ValueError(f'{path}: expected a positive finite number')


def boolean(value, path):
    if type(value) is not bool:
        raise ValueError(f'{path}: expected a boolean')


def identifiers(value, path):
    if not isinstance(value, list) or not value:
        raise ValueError(f'{path}: expected a nonempty list')
    if any(not isinstance(x, str) or not ID_RE.fullmatch(x) for x in value):
        raise ValueError(f'{path}: invalid identifier (ASCII letters/digits/_/-, max 64)')
    if len(set(value)) != len(value):
        raise ValueError(f'{path}: duplicate identifiers')


def lint_manifest(data, select=None):
    """Check a versioned, explicitly measured manifest, not a Prism file."""
    chosen = list(RULES) if select is None else select
    if not chosen or len(set(chosen)) != len(chosen) or any(x not in RULES for x in chosen):
        raise ValueError('select must contain distinct known rule codes')
    chosen = [code for code in RULES if code in chosen]
    object_fields(data, {'schema_version', 'reference', 'panels'}, '$')
    if type(data['schema_version']) is not int or data['schema_version'] != 1:
        raise ValueError('$.schema_version: supported version is integer 1')
    ref = data['reference']
    object_fields(ref, {'group_order', 'palette', 'border_width_pt', 'error_width_pt'}, '$.reference')
    identifiers(ref['group_order'], '$.reference.group_order')
    positive(ref['border_width_pt'], '$.reference.border_width_pt')
    positive(ref['error_width_pt'], '$.reference.error_width_pt')
    object_fields(ref['palette'], set(ref['group_order']), '$.reference.palette')
    for group, color in ref['palette'].items():
        if not isinstance(color, str) or not HEX_RE.fullmatch(color):
            raise ValueError(f'$.reference.palette.{group}: expected #RRGGBB')
    panels = data['panels']
    if not isinstance(panels, list) or not panels:
        raise ValueError('$.panels: expected a nonempty list')
    ids = []
    issues = []
    evaluated = {code: 0 for code in chosen}

    def check(code, condition, path):
        if code not in chosen:
            return
        evaluated[code] += 1
        if not condition:
            issues.append({'code': code, 'severity': 'error', 'path': path,
                           'message': RULES[code][1], 'fixable': False})

    for i, panel in enumerate(panels):
        path = f'$.panels[{i}]'
        object_fields(panel, {'id', 'kind', 'font', 'axis_bold', 'x_ticks', 'x_title',
                              'legends', 'stars', 'error_bars'}, path)
        ids.append(panel['id'])
        if panel['kind'] not in ('scatter', 'line', 'survival', 'bar'):
            raise ValueError(path + '.kind: expected scatter/line/survival/bar')
        text(panel['font'], path + '.font')
        boolean(panel['axis_bold'], path + '.axis_bold')
        boolean(panel['x_ticks'], path + '.x_ticks')
        if not isinstance(panel['x_title'], str):
            raise ValueError(path + '.x_title: expected text')
        check('FMT001', panel['font'] == 'Arial', path + '.font')
        check('FMT004', panel['axis_bold'] and panel['x_title'] != 'XTitle' and
              (panel['kind'] != 'scatter' or panel['x_ticks'] is False), path)
        legends = panel['legends']
        if not isinstance(legends, list) or not legends:
            raise ValueError(path + '.legends: expected a nonempty list')
        groups = []
        for j, legend in enumerate(legends):
            lp = f'{path}.legends[{j}]'
            object_fields(legend, {'group', 'label', 'audited_n', 'n_italic', 'font',
                                  'symbol', 'native', 'border_color', 'border_width_pt', 'fill'}, lp)
            for field in ('group', 'label', 'font', 'symbol', 'border_color', 'fill'):
                text(legend[field], lp + '.' + field)
            if legend['group'] not in ref['group_order']:
                raise ValueError(lp + '.group: not in reference group_order')
            groups.append(legend['group'])
            for field in ('n_italic', 'native'):
                boolean(legend[field], lp + '.' + field)
            if type(legend['audited_n']) is not int or legend['audited_n'] < 1:
                raise ValueError(lp + '.audited_n: expected a positive integer')
            positive(legend['border_width_pt'], lp + '.border_width_pt')
            if not HEX_RE.fullmatch(legend['fill']):
                raise ValueError(lp + '.fill: expected #RRGGBB')
            suffix = SAMPLE_RE.search(legend['label'])
            label_name = legend['label'][:suffix.start()].rstrip() if suffix else legend['label']
            check('NAM001', legend['group'] != 'Vav-Cre' or label_name == 'Vav-Cre', lp + '.label')
            check('LEG001', bool(suffix) and int(suffix[1]) == legend['audited_n'] and
                  legend['label'].count('(n=') == 1, lp + '.label')
            check('LEG002', legend['n_italic'], lp + '.n_italic')
            check('FMT001', legend['font'] == 'Arial', lp + '.font')
            if panel['kind'] == 'scatter':
                check('FMT002', legend['native'] and legend['symbol'] == 'circle' and
                      legend['border_color'] == 'Black' and
                      legend['border_width_pt'] == ref['border_width_pt'], lp)
            check('COL001', legend['fill'].upper() == ref['palette'][legend['group']].upper(), lp + '.fill')
        identifiers(groups, path + '.legends.group')
        expected = [x for x in ref['group_order'] if x in groups]
        check('LEG003', groups == expected, path + '.legends')
        errors = panel['error_bars']
        if errors is None:
            if panel['kind'] == 'scatter':
                raise ValueError(path + '.error_bars: scatter requires measured error-bar settings')
        else:
            object_fields(errors, {'color', 'layer', 'width_pt'}, path + '.error_bars')
            text(errors['color'], path + '.error_bars.color')
            text(errors['layer'], path + '.error_bars.layer')
            positive(errors['width_pt'], path + '.error_bars.width_pt')
            check('FMT003', errors['color'] == 'Black' and errors['layer'] == 'above_symbols' and
                  errors['width_pt'] == ref['error_width_pt'], path + '.error_bars')
        if not isinstance(panel['stars'], list):
            raise ValueError(path + '.stars: expected a list (empty if no annotations)')
        for j, star in enumerate(panel['stars']):
            sp = f'{path}.stars[{j}]'
            object_fields(star, {'text', 'font', 'bold', 'size_pt'}, sp)
            text(star['text'], sp + '.text')
            text(star['font'], sp + '.font')
            boolean(star['bold'], sp + '.bold')
            positive(star['size_pt'], sp + '.size_pt')
            check('STA001', bool(STAR_RE.fullmatch(star['text'])) and star['font'] == 'Arial' and
                  star['bold'] and star['size_pt'] == 10, sp)
    identifiers(ids, '$.panels.id')
    return {'status': 'fail' if issues else 'pass', 'diagnostics': issues,
            'selected_rules': chosen, 'rule_evaluations': evaluated,
            'full_rule_set': chosen == list(RULES), 'panel_count': len(panels),
            'scope': 'Declared manifest only; no native-file inspection, sample-count calculation, or scientific validation'}


def list_rules():
    return {'status': 'pass', 'rules': [dict(code=code, name=name, description=description,
            fixable=False) for code, (name, description) in RULES.items()]}
