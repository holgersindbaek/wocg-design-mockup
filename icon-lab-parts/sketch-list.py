# Lists every layer with export settings in a Sketch file, page by page: trail, name, class, formats,
# size and the layer id sketchtool exports by.
#   python3 icon-lab-parts/sketch-list.py ../WoCG-2.2.sketch > /tmp/exportables.txt
# Then export the ones you want as SVG:
#   /Applications/Sketch.app/Contents/MacOS/sketchtool export layers ../WoCG-2.2.sketch \
#     --items=<id>,<id> --formats=svg --use-id-for-name=YES --output=/tmp/sketch-svg
import zipfile, json, sys
path = sys.argv[1]
z = zipfile.ZipFile(path)
pages = [n for n in z.namelist() if n.startswith('pages/')]
def walk(layer, trail, out):
    name = layer.get('name', '')
    cls = layer.get('_class')
    ex = layer.get('exportOptions', {}).get('exportFormats', [])
    fr = layer.get('frame', {})
    if ex:
        fmts = ','.join(sorted(set((e.get('fileFormat') or '') + ('@%sx' % e.get('scale') if e.get('scale') not in (None, 1) else '') for e in ex)))
        out.append((trail, name, cls, fmts, round(fr.get('width', 0)), round(fr.get('height', 0)), layer.get('do_objectID')))
    for c in layer.get('layers', []) or []:
        walk(c, trail + [name], out)
for p in pages:
    d = json.loads(z.read(p))
    out = []
    walk(d, [], out)
    print('=== PAGE', d.get('name'), len(out), 'exportables')
    for t, n, c, f, w, h, oid in out:
        print('  %s | %s | %s | %s | %dx%d | %s' % (' > '.join(t[1:3]), n, c, f, w, h, oid))
