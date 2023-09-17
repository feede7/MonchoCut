import csv
import yaml
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from xlsxwriter import Workbook

from rectpack import newPacker, PackingBin
# Possible optimizing algorithims:
# https://github.com/secnot/rectpack/blob/master/rectpack/maxrects.py
#  - MaxRects
#  - MaxRectsBl
#  - MaxRectsBssf <- Default
#  - MaxRectsBaf <- Which I see as more aligning optimized
#  - MaxRectsBlsf
# from rectpack.maxrects import MaxRectsBaf as algorithm

# https://github.com/secnot/rectpack/blob/master/rectpack/guillotine.py
# Guillotine algorithms GUILLOTINE-RECT-SPLIT, Selecting one
# Axis split, and one selection criteria.
# GuillotineBssfSas
# GuillotineBssfLas
# GuillotineBssfSlas
# GuillotineBssfLlas
# GuillotineBssfMaxas
# GuillotineBssfMinas
# GuillotineBlsfSas
# GuillotineBlsfLas
# GuillotineBlsfSlas
# GuillotineBlsfLlas
# GuillotineBlsfMaxas
# GuillotineBlsfMinas
# GuillotineBafSas
# GuillotineBafLas
# GuillotineBafSlas
# GuillotineBafLlas
# GuillotineBafMaxas
# GuillotineBafMinas
from rectpack.guillotine import GuillotineBssfSlas as algorithm


def read_file(file, rects={}, mul=1, extra_name='', equivalences={}):
    assert mul > 0
    with open(file, newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=';', quotechar='|')
        for row in spamreader:
            if row[3] in equivalences:
                material = equivalences[row[3]]
            else:
                material = row[3]
            if material not in rects:
                rects[material] = {}
            pre_name = extra_name + '%'
            name = ', '.join([pre_name + a for a in row[5].split(', ')])
            assert name not in rects[material]
            rects[material][name] = {}
            height = float(row[0])
            rects[material][name]['height'] = height
            width = float(row[1])
            rects[material][name]['width'] = width
            rects[material][name]['mul'] = mul
            rects[material][name]['cantos'] = ['none', 'none', 'none', 'none']
            for j in range(4):
                canto = row[12 + j]
                if canto in equivalences:
                    rects[material][name]['cantos'][j] = equivalences[canto]
                else:
                    rects[material][name]['cantos'][j] = canto
            if rects[material][name]['cantos'] != ['', '', '', '']:
                assert width >= 120, name
                assert height >= 120, name
    return rects


def rect_pack(pieces, material, count=2):
    ESPESOR_SIERRA = 5

    BIN_SIZES = [(1830, 2600 // (2**j), (2**j)) for j in range(2)]

    # PackingBin = Enum(["BNF", "BFF", "BBF", "Global"])
    packer = newPacker(bin_algo=PackingBin.BBF, pack_algo=algorithm,
                       rotation=True)

    if count is None:
        loops = 1
    else:
        loops = count

    for ll in range(loops):
        for w, h, div in BIN_SIZES:
            name = ''
            if div == 1:
                name = 'whole'
            elif div == 2:
                name = 'half'
            elif div == 4:
                name = 'quarter'
            if count is None:
                packer.add_bin(w, h, count=float("inf"),
                               bid=f'{material}_{name}_{ll}')
            else:
                packer.add_bin(w, h, count=1,
                               bid=f'{material}_{name}_{ll}')

    for piece in pieces.keys():
        for name in piece.split(', '):
            for q in range(pieces[piece]['mul']):
                w = pieces[piece]['width'] + ESPESOR_SIERRA
                h = pieces[piece]['height'] + ESPESOR_SIERRA
                if q > 1:
                    packer.add_rect(w, h, f'{q}_{name}')
                else:
                    packer.add_rect(w, h, name)

    packer.pack()

    return packer


def analyse_packer(packer):
    bins = []
    for rect in packer.rect_list():
        b, _, _, _, _, _ = rect
        bins.append(b)
    return max(bins) + 1


def init_subplot(bins, offset, size, material):
    fig.add_subplot(1, bins, offset + 1).title.set_text(material)
    ax = plt.gca()
    ax.plot(*size)
    ax.add_patch(Rectangle((0, 0), *size,
                           edgecolor='blue',
                           facecolor='none',
                           linewidth=2,
                           ))
    return ax


def plot_packers(packers):
    from PIL.ImageColor import colormap
    from random import choice

    exclude_colors = ['snow', 'lavender', 'lavenderblush', 'lightgrey',
                      'blanchedalmond', 'ghostwhite', 'mintcream', 'ivory',
                      'white']

    while True:
        rnd_color = choice(list(colormap.keys()))
        if rnd_color not in exclude_colors:
            break
    print(rnd_color)

    # Amount of total bins
    bins = 0
    for packer in packers:
        bins += len(packer)

    offset = 0
    for packer in packers:
        for abin in packer:
            ax = init_subplot(bins, offset,
                              (abin.width, abin.height),
                              abin.bid)
            offset += 1
            for rect in abin:
                x = rect.x
                y = rect.y
                w = rect.width
                h = rect.height
                ax.add_patch(Rectangle((x, y), w, h,
                             edgecolor='white',
                             facecolor=rnd_color,
                             linewidth=1))


def plot_packer(bins, offset, packer):
    from PIL.ImageColor import colormap
    from random import choice

    exclude_colors = ['snow', 'lavender', 'lavenderblush', 'lightgrey',
                      'blanchedalmond', 'ghostwhite', 'mintcream', 'ivory',
                      'white']

    last_b = 0
    ax = init_subplot(bins, offset,
                      (packer[last_b].width, packer[last_b].height),
                      packer[last_b].bid)

    offset_rt = offset

    colors = {}
    for rect in packer.rect_list():
        b, x, y, w, h, name = rect
        obj = name.split('%')[0]
        if obj not in colors:
            while True:
                rnd_color = choice(list(colormap.keys()))
                if rnd_color not in exclude_colors:
                    break
            colors[obj] = rnd_color
        if b > last_b:
            offset_rt += 1
            ax = init_subplot(bins, offset_rt,
                              (packer[b].width, packer[b].height),
                              packer[b].bid)
            last_b = b
        ax.add_patch(Rectangle((x, y), w, h,
                               edgecolor='white',
                               facecolor=colors[obj],
                               linewidth=1,
                               ))
    return offset_rt + 1


def write_excel(workbook, material, rects, cm):
    worksheet = workbook.add_worksheet(material)

    # Baumann like
    header = ["Cantidad", "Altura", "Anchura", "ID", "Material", "Rota",
              "canto_1", "canto_2", "canto_3", "canto_4", "Nombre"]

    # write_header
    row = 0
    for col, item in enumerate(header):
        worksheet.write(row, col, item)

    row_offset = 1
    col_offset = 0
    for row, rect in enumerate(rects.items()):
        name = rect[0]
        data_dict = rect[1]
        if cm:
            height = int(data_dict['height']) / 10
            width = int(data_dict['width']) / 10
        else:
            height = data_dict['height']
            width = data_dict['width']
        mul = data_dict['mul']
        qty = mul * len(name.split(', '))
        cantos = data_dict['cantos']
        if cantos[0] == '' and cantos[1] != '':
            aux = cantos[1]
            cantos[1] = cantos[0]
            cantos[0] = aux
        if cantos[2] == '' and cantos[3] != '':
            aux = cantos[3]
            cantos[3] = cantos[2]
            cantos[2] = aux
        items_to_write = (qty, height, width, row, material, 1, *cantos, name)
        for col, item in enumerate(items_to_write):
            worksheet.write(row + row_offset, col + col_offset, item)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, default=None,
                        help="Input file.")
    parser.add_argument("--qty", type=int, default=None,
                        help="Multiple.")
    parser.add_argument("--yaml", type=str, default=None,
                        help="Yaml conf.")
    parser.add_argument("--excel", action='store_true',
                        help="Export Excel file.")
    parser.add_argument("--cm", action='store_true',
                        help="Use centimeters in exported Excel file.")
    parser.add_argument("--by_obj", action='store_true',
                        help="Plot by objects in different colors.")

    args = parser.parse_args()

    if args.yaml is None:
        assert args.file is not None
        qty = args.qty or 1

        rects = read_file(args.file, mul=qty)
    else:
        assert args.file is None
        assert args.qty is None

        with open(args.yaml, "r") as stream:
            try:
                yaml_conf = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)
        rects = {}
        equivalences = {}
        for conf in yaml_conf.keys():
            element = yaml_conf[conf]
            if conf == 'equivalences':
                for k in element:
                    mat = list(k)[0]
                    assert mat not in equivalences
                    equivalences[mat] = k[mat]
            else:
                qty = 1
                for k in element:
                    if 'path' in k:
                        file = k['path']
                    if 'qty' in k:
                        qty = k['qty']
                rects = read_file(file, rects=rects, mul=qty,
                                  extra_name=conf, equivalences=equivalences)

    fig = plt.figure()
    packers = []
    bins = 0

    # Get total of used bins to set the following subplots
    # In addition, if asked, one excel is generated for each material
    if args.excel:
        workbook = Workbook('placas.xlsx')

    for i, material in enumerate(rects.keys()):
        packer = rect_pack(rects[material], material)
        packers.append(packer)
        bins += analyse_packer(packer)
        if args.excel:
            write_excel(workbook, material, rects[material], args.cm)

    if args.excel:
        workbook.close()

    if args.by_obj:
        offset = 0
        for i, material in enumerate(rects.keys()):
            offset = plot_packer(bins, offset, packers[i])
    else:
        plot_packers(packers)
    plt.show()
