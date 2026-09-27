import type { ThemeRegistration } from 'shiki';

/**
 * The two Quidra syntax themes. Deliberately narrow palette: one blue family
 * for keywords, one teal for types, one warm tone for literals, grey for
 * punctuation. The tokens that carry Quidra's semantic distinctions
 * (`try`, `&`, the union bar `|`) get the brand accent in a heavier weight.
 */

type Palette = {
  fg: string;
  bg: string;
  comment: string;
  literal: string;
  constant: string;
  keyword: string;
  semantic: string;
  type: string;
  namespace: string;
  functionName: string;
  operator: string;
  punctuation: string;
};

const dark: Palette = {
  fg: '#e6e9ef',
  bg: '#0e121a',
  comment: '#7a8494',
  literal: '#d4b06a',
  constant: '#c8d0d8',
  keyword: '#79a6ff',
  semantic: '#4f8cff',
  type: '#7fc4d6',
  namespace: '#9fb9d6',
  functionName: '#e6e9ef',
  operator: '#a9b1be',
  punctuation: '#7d8696',
};

const light: Palette = {
  fg: '#0c1526',
  bg: '#f6f8fb',
  comment: '#6b7280',
  literal: '#7a4f00',
  constant: '#344054',
  keyword: '#1a4fc4',
  semantic: '#0b57d0',
  type: '#0e7490',
  namespace: '#3b5573',
  functionName: '#0c1526',
  operator: '#475467',
  punctuation: '#667085',
};

function build(name: string, type: 'light' | 'dark', p: Palette): ThemeRegistration {
  // Shiki (via vscode-textmate) reads token rules from `settings` when that
  // array exists and falls back to `tokenColors` otherwise, so both are set
  // to the same list: a scope-less default entry followed by the scoped rules.
  const rules: NonNullable<ThemeRegistration['tokenColors']> = [
    { settings: { foreground: p.fg, background: p.bg } },
    { scope: ['comment', 'comment.line.double-slash.quidra', 'punctuation.definition.comment.quidra'], settings: { foreground: p.comment } },
    {
      scope: [
        'string',
        'string.quoted.double.quidra',
        'punctuation.definition.string.begin.quidra',
        'punctuation.definition.string.end.quidra',
        'constant.character.escape.quidra',
        'constant.numeric',
        'constant.numeric.quidra',
      ],
      settings: { foreground: p.literal },
    },
    {
      scope: [
        'meta.interpolation.quidra',
        'punctuation.section.interpolation.begin.quidra',
        'punctuation.section.interpolation.end.quidra',
        'constant.other.format-spec.quidra',
      ],
      settings: { foreground: p.operator },
    },
    {
      scope: [
        'constant.language',
        'constant.language.boolean.quidra',
        'constant.language.none.quidra',
        'constant.language.void.quidra',
        'constant.language.control-character.quidra',
      ],
      settings: { foreground: p.constant, fontStyle: 'bold' },
    },
    {
      scope: [
        'keyword.control',
        'keyword.control.quidra',
        'keyword.control.import.quidra',
        'keyword.declaration.quidra',
        'storage.modifier.quidra',
        'keyword.operator.logical.quidra',
        'keyword.operator.bitwise.quidra',
        'keyword.other',
      ],
      settings: { foreground: p.keyword },
    },
    {
      scope: ['keyword.control.try.quidra', 'keyword.operator.address.quidra', 'keyword.operator.union.quidra', 'meta.shape.wildcard.quidra'],
      settings: { foreground: p.semantic, fontStyle: 'bold' },
    },
    {
      scope: [
        'storage.type',
        'storage.type.primitive.quidra',
        'storage.type.generic-constraint.quidra',
        'entity.name.type',
        'entity.name.type.quidra',
        'entity.name.type.parameter.quidra',
        'entity.name.type.class',
      ],
      settings: { foreground: p.type },
    },
    { scope: ['support.namespace', 'support.namespace.quidra', 'support.class'], settings: { foreground: p.namespace } },
    { scope: ['entity.name.function', 'entity.name.function.quidra'], settings: { foreground: p.functionName, fontStyle: 'bold' } },
    { scope: ['support.function', 'support.function.quidra', 'variable.parameter.quidra'], settings: { foreground: p.fg } },
    {
      scope: ['keyword.operator.assignment.quidra', 'keyword.operator.comparison.quidra', 'keyword.operator.arithmetic.quidra', 'keyword.operator'],
      settings: { foreground: p.operator },
    },
    {
      scope: [
        'punctuation',
        'punctuation.separator.quidra',
        'punctuation.section.brackets.begin.quidra',
        'punctuation.section.brackets.end.quidra',
        'punctuation.section.parens.begin.quidra',
        'punctuation.section.parens.end.quidra',
        'punctuation.section.angle.begin.quidra',
        'punctuation.section.angle.end.quidra',
        'punctuation.accessor.quidra',
      ],
      settings: { foreground: p.punctuation },
    },
    /* Shell blocks (Shiki's bundled bash grammar) */
    { scope: ['source.shell', 'source.shell variable.other'], settings: { foreground: p.fg } },
    { scope: ['source.shell support.function.builtin', 'source.shell entity.name.command', 'source.shell entity.name.function'], settings: { foreground: p.keyword } },
    { scope: ['source.shell comment'], settings: { foreground: p.comment } },
    { scope: ['source.shell string'], settings: { foreground: p.literal } },
    { scope: ['source.shell constant.other.option', 'source.shell keyword.operator'], settings: { foreground: p.operator } },
  ];
  return {
    name,
    type,
    colors: { 'editor.background': p.bg, 'editor.foreground': p.fg },
    settings: rules,
    tokenColors: rules,
  };
}

export const quidraDark = build('quidra-dark', 'dark', dark);
export const quidraLight = build('quidra-light', 'light', light);
export const themes = { light: quidraLight, dark: quidraDark };
