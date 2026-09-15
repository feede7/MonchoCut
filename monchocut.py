import csv
from random import choice

import matplotlib.pyplot as plt
import yaml
from matplotlib.patches import Rectangle
from PIL.ImageColor import colormap
from xlsxwriter import Workbook

from rectpack import PackingBin, newPacker
from rectpack.guillotine import GuillotineBssfSlas as algorithm

SIERRA_THICKNESS = 5
BIN_SIZES = [
    (1830, 2600 // 1, 1),
    (1830, 2600 // 1, 1),
    (1830, 2600 // 1, 1),
    (1830, 2600 // 2, 2),
    (1830, 2600 // 2, 2),
]
EXCLUDE_COLORS = {
    'snow', 'lavender', 'lavenderblush', 'lightgrey',
    'blanchedalmond', 'ghostwhite', 'mintcream', 'ivory', 'white'
}


def random_color():
    while True:
        color = choice(list(colormap.keys()))
        if color not in EXCLUDE_COLORS:
            return color


def read_file(file, rects=None, mul=1, extra_name='', equivalences=None):
    rects = {} if rects is None else rects
    equivalences = {} if equivalences is None else equivalences
    assert mul > 0

    with open(file, mode='r', encoding='utf-8', errors='replace', newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=';', quotechar='|')
        for r, row in enumerate(spamreader):
            if len(row) < 16:
                row = row + [''] * (16 - len(row))

            if len(row) < 16:
                raise ValueError(f'Fila {r} con columnas insuficientes: {row}')

            material = equivalences.get(row[3], row[3])
            if material not in rects:
                rects[material] = {}

            pre_name = extra_name + '%'
            name = ', '.join([pre_name + a for a in row[5].split(', ')])
            name += f'_{r}'
            msg = f'name: {name}, recs: {rects}, material: {material}'
            assert name not in rects[material], msg

            rects[material][name] = {
                'height': float(row[0]),
                'width': float(row[1]),
                'mul': mul,
                'cantos': ['none', 'none', 'none', 'none'],
            }

            for j in range(4):
                canto = row[12 + j] if 12 + j < len(row) else ''
                rects[material][name]['cantos'][j] = equivalences.get(canto, canto)

    return rects


def rect_pack(pieces, material, count=1):
    packer = newPacker(bin_algo=PackingBin.BBF, pack_algo=algorithm, rotation=True)
    loops = 1 if count is None else count

    for ll in range(loops):
        for w, h, div in BIN_SIZES:
            div_name = {1: 'whole', 2: 'half', 4: 'quarter'}.get(div, '')
            if count is None:
                packer.add_bin(w, h, count=float('inf'), bid=f'{material}_{div_name}_{ll}')
            else:
                packer.add_bin(w, h, count=1, bid=f'{material}_{div_name}_{ll}')

    for piece_name, piece_data in pieces.items():
        for name in piece_name.split(', '):
            for q in range(piece_data['mul']):
                w = piece_data['width'] + SIERRA_THICKNESS
                h = piece_data['height'] + SIERRA_THICKNESS
                rect_name = f'{q}_{name}' if q > 1 else name
                packer.add_rect(w, h, rect_name)

    packer.pack()
    return packer


def analyse_packer(packer):
    bins = []
    for rect in packer.rect_list():
        b, _, _, _, _, _ = rect
        bins.append(b)
    return max(bins) + 1 if bins else 0


def init_subplot(fig, bins, offset, size, material):
    fig.add_subplot(1, bins, offset + 1).title.set_text(material)
    ax = plt.gca()
    ax.plot(*size)
    ax.add_patch(Rectangle((0, 0), *size,
                           edgecolor='blue',
                           facecolor='none',
                           linewidth=2))
    return ax


def plot_packers(fig, packers):
    bins = sum(len(packer) for packer in packers)
    offset = 0
    color = random_color()

    for packer in packers:
        for abin in packer:
            ax = init_subplot(fig, bins, offset, (abin.width, abin.height), abin.bid)
            offset += 1
            for rect in abin:
                ax.add_patch(Rectangle((rect.x, rect.y), rect.width, rect.height,
                                       edgecolor='white',
                                       facecolor=color,
                                       linewidth=1))


def plot_packer(fig, bins, offset, packer):
    last_b = 0
    ax = init_subplot(fig, bins, offset, (packer[last_b].width, packer[last_b].height), packer[last_b].bid)
    offset_rt = offset
    colors = {}

    for rect in packer.rect_list():
        b, x, y, w, h, name = rect
        obj = name.split('%')[0]
        if obj not in colors:
            colors[obj] = random_color()

        if b > last_b:
            offset_rt += 1
            ax = init_subplot(fig, bins, offset_rt, (packer[b].width, packer[b].height), packer[b].bid)
            last_b = b

        ax.add_patch(Rectangle((x, y), w, h,
                               edgecolor='white',
                               facecolor=colors[obj],
                               linewidth=1))

    return offset_rt + 1


def write_excel(workbook, material, rects, cm):
    worksheet = workbook.add_worksheet(material)
    header = ["Cantidad", "Altura", "Anchura", "ID", "Material", "Rota",
              "canto_1", "canto_2", "canto_3", "canto_4", "Nombre"]

    for col, item in enumerate(header):
        worksheet.write(0, col, item)

    for row, rect in enumerate(rects.items(), start=1):
        name, data_dict = rect
        height = int(data_dict['height']) / 10 if cm else data_dict['height']
        width = int(data_dict['width']) / 10 if cm else data_dict['width']
        mul = data_dict['mul']
        qty = mul * len(name.split(', '))
        cantos = list(data_dict['cantos'])

        if "Puerta" in name:
            cantos = ['X'] * 4

        if cantos[0] == '' and cantos[1] != '':
            cantos[1], cantos[0] = cantos[0], cantos[1]
        if cantos[2] == '' and cantos[3] != '':
            cantos[3], cantos[2] = cantos[2], cantos[3]

        items_to_write = (qty, height, width, row - 1, material, 1, *cantos, name)
        for col, item in enumerate(items_to_write):
            worksheet.write(row, col, item)


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--file', type=str, default=None, help='Input file.')
    parser.add_argument('--qty', type=int, default=None, help='Multiple.')
    parser.add_argument('--yaml', type=str, default=None, help='Yaml conf.')
    parser.add_argument('--excel', action='store_true', help='Export Excel file.')
    parser.add_argument('--cm', action='store_true', help='Use centimeters in exported Excel file.')
    parser.add_argument('--by_obj', action='store_true', help='Plot by objects in different colors.')
    args = parser.parse_args()

    if args.yaml is None:
        assert args.file is not None, 'Debe indicar --file o --yaml.'
        qty = args.qty or 1
        rects = read_file(args.file, mul=qty)
    else:
        assert args.file is None, 'No combine --file con --yaml.'
        assert args.qty is None, 'No combine --qty con --yaml.'

        with open(args.yaml, 'r', encoding='utf-8') as stream:
            try:
                yaml_conf = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                raise RuntimeError(f'YAML inválido: {exc}') from exc

        if yaml_conf is None:
            raise ValueError('El archivo YAML está vacío.')

        rects = {}
        equivalences = {}
        for conf, element in yaml_conf.items():
            if conf == 'equivalences':
                for k in element:
                    mat = next(iter(k))
                    equivalences[mat] = k[mat]
                    print(f'instead {mat} I will use {k[mat]}')
            else:
                file_name = None
                qty = 1
                for k in element:
                    if 'path' in k:
                        file_name = k['path']
                    if 'qty' in k:
                        qty = k['qty']
                if file_name is None:
                    raise ValueError(f'Falta path en la configuración {conf}.')
                rects = read_file(file_name, rects=rects, mul=qty, extra_name=conf, equivalences=equivalences)

    fig = plt.figure()
    packers = []
    total_bins = 0

    if args.excel:
        workbook = Workbook('placas.xlsx')

    for material in rects.keys():
        packer = rect_pack(rects[material], material)
        packers.append(packer)
        total_bins += analyse_packer(packer)
        if args.excel:
            write_excel(workbook, material, rects[material], args.cm)

    if args.excel:
        workbook.close()

    if args.by_obj:
        offset = 0
        for material, packer in zip(rects.keys(), packers):
            offset = plot_packer(fig, total_bins, offset, packer)
    else:
        plot_packers(fig, packers)

    plt.show()


if __name__ == '__main__':
    main()
