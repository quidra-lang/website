import { createHighlighter, type Highlighter, type LanguageRegistration, type ShikiTransformer } from 'shiki';
import quidraGrammar from './quidra.tmLanguage.json';
import { quidraDark, quidraLight } from './shiki-theme';

/**
 * One Shiki highlighter for the whole build. Quidra uses the project's own
 * TextMate grammar; shell and JSON snippets use Shiki's bundled grammars.
 * Adjacent tokens with identical styling are merged to keep the HTML small.
 */
let instance: Promise<Highlighter> | undefined;

function highlighter(): Promise<Highlighter> {
  instance ??= createHighlighter({
    langs: [quidraGrammar as unknown as LanguageRegistration, 'bash', 'json'],
    themes: [quidraLight, quidraDark],
  });
  return instance;
}

export type CodeLang = 'quidra' | 'bash' | 'json' | 'text';

export async function highlight(code: string, lang: CodeLang, transformers: ShikiTransformer[] = [], label = 'code'): Promise<string> {
  const shiki = await highlighter();
  return shiki.codeToHtml(code, {
    lang: lang === 'text' ? 'text' : lang,
    themes: { light: 'quidra-light', dark: 'quidra-dark' },
    defaultColor: false,
    mergeSameStyleTokens: true,
    transformers: [
      ...transformers,
      {
        name: 'quidra-pre',
        pre(node) {
          // Focusable so keyboard users can scroll long lines; named so the
          // focus stop is announced meaningfully.
          this.addClassToHast(node, 'astro-code');
          node.properties.tabindex = '0';
          node.properties.role = 'region';
          node.properties['aria-label'] = label;
          delete node.properties.style;
        },
      },
    ],
  });
}
