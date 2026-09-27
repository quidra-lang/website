import type { ShikiTransformer } from 'shiki';

export interface Annotation {
  /** 1-based source line the marker is attached to. */
  line: number;
  /** The token or phrase the note is about, shown in monospace. */
  token: string;
  /** One or two plain sentences. */
  text: string;
}

/**
 * Adds a numbered marker to annotated lines. The number matches the
 * corresponding item in the <ol class="annotations"> rendered beside the code.
 */
export function annotationTransformer(annotations: Annotation[]): ShikiTransformer {
  const byLine = new Map<number, number>();
  annotations.forEach((a, index) => byLine.set(a.line, index + 1));
  return {
    name: 'quidra-annotations',
    line(node, line) {
      const marker = byLine.get(line);
      if (marker === undefined) return;
      this.addClassToHast(node, 'is-annotated');
      // The marker sits in a gutter at the start of the line so it stays
      // visible on narrow screens where long lines scroll horizontally.
      node.children.unshift({
        type: 'element',
        tagName: 'span',
        properties: { className: ['ann-mark'], 'aria-hidden': 'true' },
        children: [{ type: 'text', value: String(marker) }],
      });
    },
    pre(node) {
      this.addClassToHast(node, 'has-annotations');
    },
  };
}
