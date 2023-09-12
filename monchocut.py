import csv
from rectpack import newPacker
# Possible optimizing algorithims:
# https://github.com/secnot/rectpack/blob/master/rectpack/maxrects.py
#  - MaxRects
#  - MaxRectsBl
#  - MaxRectsBssf <- Default
#  - MaxRectsBaf <- Which I see as more aligning optimized
#  - MaxRectsBlsf
from rectpack.maxrects import MaxRectsBaf as maxrect
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import yaml
from xlsxwriter import Workbook


def read_file(file, rects={}, mul=1, extra_name='', equivalences={}):
    ESPESOR_SIERRA = 5
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
            height = row[0]
            rects[material][name]['height'] = float(height) + ESPESOR_SIERRA
            width = row[1]
            rects[material][name]['width'] = float(width) + ESPESOR_SIERRA
            rects[material][name]['mul'] = mul
            rects[material][name]['cantos'] = ['none', 'none', 'none', 'none']
            for j in range(4):
                canto = row[12 + j]
                if canto in equivalences:
                    rects[material][name]['cantos'][j] = equivalences[canto]
                else:
                    rects[material][name]['cantos'][j] = canto
    return rects


def rect_pack(pieces):
    BIN_SIZE = (1830, 2600)

    packer = newPacker(pack_algo=maxrect, rotation=True)

    packer.add_bin(*BIN_SIZE, count=float("inf"))

    for piece in pieces.keys():
        # print(piece)
        for name in piece.split(', '):
            for q in range(pieces[piece]['mul']):
                w = pieces[piece]['width']
                h = pieces[piece]['height']
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


def plot_packer(bins, offset, material, packer):
    from PIL.ImageColor import colormap
    from random import choice

    BIN_SIZE = (1830, 2600)

    exclude_colors = ['snow', 'lavender', 'lavenderblush', 'lightgrey',
                      'blanchedalmond', 'ghostwhite', 'mintcream', 'ivory',
                      'white']

    ax = init_subplot(bins, offset, BIN_SIZE, material)

    last_b = 0
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
            ax = init_subplot(bins, offset_rt, BIN_SIZE, material)
            last_b = b
        ax.add_patch(Rectangle((x, y), w, h,
                               edgecolor='white',
                               facecolor=colors[obj],
                               linewidth=1,
                               ))
    return offset_rt + 1


def write_excel(workbook, material, rects, cm):
    worksheet = workbook.add_worksheet(material)

    header = ["Nombre", "Altura", "Anchura", "Cantidad",
              "canto_1", "canto_2", "canto_3", "canto_4"]

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
        items_to_write = (name, height, width, qty, *cantos)
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
        packer = rect_pack(rects[material])
        packers.append(packer)
        bins += analyse_packer(packer)
        if args.excel:
            write_excel(workbook, material, rects[material], args.cm)

    if args.excel:
        workbook.close()

    offset = 0
    for i, material in enumerate(rects.keys()):
        offset = plot_packer(bins, offset, material, packers[i])
    plt.show()
