import data from '../data/procesamiento.json';

/**
 * Quién procesa y quién deriva cada examen (src/data/procesamiento.json, generado por
 * scripts/build-procesamiento.py). Solo se registra lo que el prestador declara públicamente;
 * la ausencia de registro significa "no informado", nunca "se procesa en el propio lugar".
 */
export interface Procesamiento {
  exam: string;
  rol: 'procesa' | 'deriva';
  quien: string;
  destino?: string;
  metodo?: string;
  fuente: string;
  verificado: string;
  nota?: string;
}

const byExam = new Map<string, Procesamiento[]>();
for (const r of data as Procesamiento[]) {
  const list = byExam.get(r.exam) ?? [];
  list.push(r);
  byExam.set(r.exam, list);
}

export function getProcesamiento(examId: string): { procesan: Procesamiento[]; derivan: Procesamiento[] } {
  const all = byExam.get(examId) ?? [];
  return { procesan: all.filter((r) => r.rol === 'procesa'), derivan: all.filter((r) => r.rol === 'deriva') };
}
