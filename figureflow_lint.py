"""Explicit figure-manifest checks; never edits or introspects native projects."""
import re


RULES = {
    'NAM001': ('canonical-control', 'Use the canonical names declared by the active profile.'),
    'LEG001': ('sample-count', 'Each legend needs one positive (n=N), matching audited_n.'),
    'LEG002': ('sample-italics', 'Match the active profile sample-count italic policy.'),
    'LEG003': ('legend-order', 'Legend group IDs must follow the declared group_order.'),
    'FMT001': ('arial', 'All reported text must use the profile font or one consistent measured font.'),
    'FMT002': ('native-symbol-border', 'Scatter circles need black reference-width borders and the profile native-object policy.'),
    'FMT003': ('error-bars', 'Scatter error bars must be black, above symbols, and match the reference width.'),
    'FMT004': ('axes', 'Axes must match the profile bold/tick policy and have no XTitle placeholder.'),
    'STA001': ('star-format', 'Stars must match the profile font/bold/size and contain 1–4 stars or ns.'),
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


PROFILES = {
    'uwm': dict(font='Arial', canonical_names={'Vav-Cre': 'Vav-Cre'}, n_italic=True,
                axis_bold=True, scatter_x_ticks=False, require_native=True,
                star_size_pt=10, star_bold=True),
    'generic': dict(font=None, canonical_names={}, n_italic=None,
                    axis_bold=None, scatter_x_ticks=None, require_native=False,
                    star_size_pt=10, star_bold=True),
}


def resolve_profile(profile):
    if isinstance(profile, str):
        if profile not in PROFILES:
            raise ValueError('Unknown style profile')
        return dict(PROFILES[profile]), profile
    object_fields(profile, set(PROFILES['generic']), '$profile')
    if profile['font'] is not None: text(profile['font'], '$profile.font')
    if not isinstance(profile['canonical_names'], dict):
        raise ValueError('canonical_names must map machine IDs to display names')
    for k, v in profile['canonical_names'].items():
        text(k, '$profile.canonical_names.key'); text(v, '$profile.canonical_names.value')
    for field in ('n_italic', 'axis_bold', 'scatter_x_ticks'):
        if profile[field] is not None: boolean(profile[field], '$profile.'+field)
    boolean(profile['require_native'], '$profile.require_native')
    boolean(profile['star_bold'], '$profile.star_bold')
    positive(profile['star_size_pt'], '$profile.star_size_pt')
    return dict(profile), 'custom'


def lint_manifest(data, select=None, profile="uwm"):
    """Check a versioned, explicitly measured manifest, not a Prism file."""
    policy, profile_name = resolve_profile(profile)
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
    expected_font = policy['font'] or panels[0].get('font')
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
        check('FMT001', panel['font'] == expected_font, path + '.font')
        check('FMT004', (policy['axis_bold'] is None or panel['axis_bold'] == policy['axis_bold']) and panel['x_title'] != 'XTitle' and
              (panel['kind'] != 'scatter' or policy['scatter_x_ticks'] is None or panel['x_ticks'] == policy['scatter_x_ticks']), path)
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
            check('NAM001', legend['group'] not in policy['canonical_names'] or label_name == policy['canonical_names'][legend['group']], lp + '.label')
            check('LEG001', bool(suffix) and int(suffix[1]) == legend['audited_n'] and
                  legend['label'].count('(n=') == 1, lp + '.label')
            check('LEG002', policy['n_italic'] is None or legend['n_italic'] == policy['n_italic'], lp + '.n_italic')
            check('FMT001', legend['font'] == expected_font, lp + '.font')
            if panel['kind'] == 'scatter':
                check('FMT002', (legend['native'] or not policy['require_native']) and legend['symbol'] == 'circle' and
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
            check('STA001', bool(STAR_RE.fullmatch(star['text'])) and star['font'] == expected_font and
                  star['bold'] == policy['star_bold'] and star['size_pt'] == policy['star_size_pt'], sp)
    identifiers(ids, '$.panels.id')
    return {'status': 'fail' if issues else 'pass', 'diagnostics': issues,
            'profile': profile_name, 'profile_settings': policy, 'selected_rules': chosen, 'rule_evaluations': evaluated,
            'full_rule_set': chosen == list(RULES), 'panel_count': len(panels),
            'scope': 'Declared manifest only; no native-file inspection, sample-count calculation, or scientific validation'}


def list_rules():
    return {'status': 'pass', 'rules': [dict(code=code, name=name, description=description,
            fixable=False) for code, (name, description) in RULES.items()]}
