#!/usr/bin/env python3
"""
Genera src/data/procesamiento.json: quién PROCESA y quién DERIVA cada examen (sin precios).

Fuentes (todas públicas, con fecha):
  * docs/fuentes/bklab-directorio-*.csv   -> BKLAB (Barnafi Krause) procesa el examen en sus propias instalaciones.
  * docs/fuentes/derivaciones-*.csv       -> prestadores que declaran en su arancel que derivan el examen, y a quién.
    Columnas: exam_id, quien, destino, fuente_url, verificado, nota

Solo se registra lo que el prestador DECLARA. La ausencia de un registro no significa que el examen se procese
en el propio lugar: significa "no informado".

Uso:
  python scripts/build-procesamiento.py [--bklab CSV] [--deriv CSV]
"""
import argparse, csv, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BKLAB_NAME = 'BKLAB (Barnafi Krause)'


def exam_id(codigo_fonasa, codigo_bklab):
    c = codigo_fonasa.strip()
    if c.lower().startswith('sin'):
        return 'sf-' + codigo_bklab.strip().lower()
    d = c.zfill(7)
    return f'{d[:2]}-{d[2:4]}-{d[4:]}'


def latest(pattern):
    files = sorted((ROOT / 'docs/fuentes').glob(pattern))
    if not files:
        sys.exit(f'No hay archivos {pattern} en docs/fuentes')
    return files[-1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bklab', default=None)
    ap.add_argument('--deriv', default=None)
    a = ap.parse_args()
    bk = Path(a.bklab) if a.bklab else latest('bklab-directorio-*.csv')
    dv = Path(a.deriv) if a.deriv else latest('derivaciones-*.csv')

    catalog = set()
    for f in ('fonasa-mle-2026.json', 'examenes-sin-fonasa.json'):
        catalog |= {x['id'] for x in json.loads((ROOT / 'src/data' / f).read_text(encoding='utf-8'))}

    records, skipped = [], []
    for r in csv.DictReader(open(bk, encoding='utf-8')):
        eid = exam_id(r['codigo_fonasa'], r['codigo_bklab'])
        if eid not in catalog:
            skipped.append((eid, r['nombre']))
            continue
        records.append({'exam': eid, 'rol': 'procesa', 'quien': BKLAB_NAME, 'metodo': r['metodo'],
                        'fuente': r['ficha'], 'verificado': r['verificado']})
    for r in csv.DictReader(open(dv, encoding='utf-8')):
        if r['exam_id'] not in catalog:
            sys.exit(f"Examen inexistente en el catálogo: {r['exam_id']}")
        rec = {'exam': r['exam_id'], 'rol': 'deriva', 'quien': r['quien'], 'destino': r['destino'],
               'fuente': r['fuente_url'], 'verificado': r['verificado']}
        if r['nota']:
            rec['nota'] = r['nota']
        records.append(rec)

    # Un examen puede tener varios registros BKLAB (variantes con otro método): se deja uno por examen y laboratorio.
    seen, out = set(), []
    for rec in records:
        k = (rec['exam'], rec['rol'], rec['quien'])
        if k in seen:
            continue
        seen.add(k)
        out.append(rec)
    out.sort(key=lambda r: (r['exam'], r['rol'], r['quien']))
    lines = ',\n'.join(' ' + json.dumps(r, ensure_ascii=False) for r in out)
    (ROOT / 'src/data/procesamiento.json').write_text('[\n' + lines + '\n]\n', encoding='utf-8')
    print(f'{len(out)} registros ({sum(r["rol"]=="procesa" for r in out)} procesa, {sum(r["rol"]=="deriva" for r in out)} deriva)')
    for s in skipped:
        print('  omitido (no está en el catálogo):', s)


main()
