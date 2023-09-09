import csv
from rectpack import newPacker
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import yaml


def read_file(file, rects={}, mul=1, extra_name=''):
    ESPESOR_SIERRA = 5
    assert mul > 0
    with open(file, newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=';', quotechar='|')
        for row in spamreader:
            material = row[3]
            if material not in rects:
                rects[material] = {}
            name = extra_name + '_' + row[5]
            assert name not in rects[material]
            rects[material][name] = {}
            height = row[0]
            rects[material][name]['height'] = float(height) + ESPESOR_SIERRA
            width = row[1]
            rects[material][name]['width'] = float(width) + ESPESOR_SIERRA
            rects[material][name]['qty'] = mul
    return rects


def rect_pack(pieces):
    BIN_SIZE = (1830, 2600)

    packer = newPacker(rotation=True)

    packer.add_bin(*BIN_SIZE, count=float("inf"))

    for piece in pieces.keys():
        # print(piece)
        for name in piece.split(', '):
            for q in range(pieces[piece]['qty']):
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
    BIN_SIZE = (1830, 2600)

    ax = init_subplot(bins, offset, BIN_SIZE, material)

    last_b = 0
    offset_rt = offset
    for rect in packer.rect_list():
        b, x, y, w, h, name = rect
        # print(f"Bin {b}, Pieza {name}: {w}x{h} en posición ({x}, {y})")
        if b > last_b:
            offset_rt += 1
            ax = init_subplot(bins, offset_rt, BIN_SIZE, material)
            last_b = b
        ax.add_patch(Rectangle((x, y), w, h,
                               edgecolor='orange',
                               facecolor='none',
                               linewidth=1,
                               ))
    return offset_rt + 1


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, default=None,
                        help="Input file.")
    parser.add_argument("--qty", type=int, default=None,
                        help="Multiple.")
    parser.add_argument("--yaml", type=str, default=None,
                        help="Yaml conf.")

    args = parser.parse_args()

    if args.yaml is None:
        assert args.file is not None
        qty = args.qty or 1

        print(args.file)
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
        for conf in yaml_conf.keys():
            element = yaml_conf[conf]
            qty = 1
            for k in element:
                if 'path' in k:
                    file = k['path']
                if 'qty' in k:
                    qty = k['qty']
            rects = read_file(file, rects=rects, mul=qty, extra_name=conf)

    fig = plt.figure()
    packers = []
    bins = 0
    for i, material in enumerate(rects.keys()):
        packer = rect_pack(rects[material])
        packers.append(packer)
        bins += analyse_packer(packer)

    offset = 0
    for i, material in enumerate(rects.keys()):
        offset = plot_packer(bins, offset, material, packers[i])
    plt.show()
