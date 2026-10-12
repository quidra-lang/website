import benchmarks from '../data/benchmarks.json';

export interface BenchmarkSource {
  label: string;
  url: string;
}

export interface LanguageAnalysis {
  id: string;
  name: string;
  score: number;
  explanation: string[];
  facts: { label: string; value: string | number }[];
  sources: BenchmarkSource[];
  caveats: string[];
}

export interface RequirementAnalysis {
  id: string;
  title: string;
  description: string;
  method: string;
  comparison_notes: string[];
  languages: LanguageAnalysis[];
}

export interface EvaluationAnalysis {
  id: string;
  introduction: string;
  aggregation: string;
  requirements: RequirementAnalysis[];
}

export interface BenchmarkAnalysisDocument {
  schema_version: number;
  run_id: string;
  evaluated_commit: string;
  source_commit: string;
  evaluations: EvaluationAnalysis[];
}

export type BenchmarkEvaluation = (typeof benchmarks.evaluations)[number];

export const evaluationPath = (id: string) => `/benchmarks/${id.replaceAll('_', '-')}/`;
export const requirementAnchor = (id: string) => id.replace(/[._]/g, '-');
export const formatScore = (score: number) => score.toFixed(2);
export const formatDelta = (delta: number) => `${delta < 0 ? '−' : delta > 0 ? '+' : ''}${Math.abs(delta).toFixed(2)}`;
export const ordinal = (n: number) => `${n}${['th', 'st', 'nd', 'rd'][(n % 100 > 10 && n % 100 < 14) || n % 10 > 3 ? 0 : n % 10]}`;

export const languageVersion = (id: string) => benchmarks.languages.find((language) => language.id === id)?.version;

/**
 * Select the strongest non-Quidra languages independently for every row.
 * Scores and tie membership come from the published rankings, never prose.
 * Fail the static build if an evidence panel is missing or disagrees with it.
 */
export function requirementComparisons(evaluation: BenchmarkEvaluation, analysis: EvaluationAnalysis) {
  const quidra = benchmarks.languages.find((language) => language.id.startsWith('quidra_'));
  if (!quidra) throw new Error('The benchmark has no Quidra language.');
  if (analysis.id !== evaluation.id || analysis.requirements.length !== evaluation.requirements.length) {
    throw new Error(`Analysis requirements do not match ${evaluation.id}.`);
  }

  return evaluation.requirements.map((requirement) => {
    const matches = analysis.requirements.filter((item) => item.id === requirement.id);
    if (matches.length !== 1) throw new Error(`Expected one analysis for ${evaluation.id}/${requirement.id}.`);
    const evidence = matches[0];
    const scores: Record<string, number> = requirement.scores;
    const otherLanguages = benchmarks.languages.filter((language) => language.id !== quidra.id);
    const bestOtherScore = Math.max(...otherLanguages.map((language) => scores[language.id]));
    const leaders = otherLanguages.filter((language) => scores[language.id] === bestOtherScore);
    const selectedLanguages = [quidra, ...leaders];

    if (evidence.languages.length !== selectedLanguages.length) {
      throw new Error(`Evidence must include Quidra and every tied leader for ${evaluation.id}/${requirement.id}.`);
    }

    const languageEvidence = selectedLanguages.map((language) => {
      const entries = evidence.languages.filter((item) => item.id === language.id);
      if (entries.length !== 1 || entries[0].score !== scores[language.id] || entries[0].name !== language.name) {
        throw new Error(`Evidence disagrees with published data for ${evaluation.id}/${requirement.id}/${language.id}.`);
      }
      return entries[0];
    });

    return {
      ...evidence,
      anchor: requirementAnchor(requirement.id),
      weight: requirement.weight,
      category: requirement.category,
      quidra: languageEvidence[0],
      leaders: languageEvidence.slice(1),
      bestOtherScore,
      delta: Math.round((scores[quidra.id] - bestOtherScore) * 100) / 100,
    };
  });
}
