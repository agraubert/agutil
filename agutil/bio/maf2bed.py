import argparse
from subprocess import call
import sys
import csv


def bedkey(args):
    args.keys = set(args.keys)
    output = []
    reader = csv.DictReader(args.input, delimiter='\t')

    for row in reader:
        if row['Key'] in args.keys:
            if not args.suppress:
                print(row)
            output.append(row)

    args.input.close()
    return output


def maf2bed(args):
    if args.v and sys.platform == "win32":
        reader = open(args.input.name, mode='r')
        args.v = len([False for row in reader])
        reader.close()
    elif args.v:
        from subprocess import check_output
        args.v = int(
            check_output(
                ['wc -l %s' % args.input.name],
                shell=True
            ).decode().split()[0]
        )
    key_file = None
    if not args.skip_keyfile:
        key_file = open(args.output.name+".key", mode='w')
    reader = csv.DictReader(args.input, delimiter='\t')
    keyWriter = None
    writer_fields = reader.fieldnames if args.skip_keyfile else [
        "Chromosome",
        "Start_position",
        "End_position",
        "Key"
    ]
    writer = csv.DictWriter(
        args.output,
        writer_fields,
        delimiter='\t',
        lineterminator='\n'
    )
    if not args.skip_keyfile:
        keyWriter = csv.DictWriter(
            key_file,
            ["Key"] + reader.fieldnames,
            delimiter='\t',
            lineterminator='\n'
        )
        keyWriter.writeheader()
    else:
        writer.writeheader()

    i = 0
    bar = None
    if args.v:
        try:
            from .. import status_bar
        except SystemError:
            import os.path
            sys.path.append(
                os.path.dirname(
                    os.path.dirname(
                        os.path.dirname(
                            os.path.abspath(__file__)
                        )
                    )
                )
            )
            from agutil import status_bar
        bar = status_bar(
            args.v,
            show_percent=True,
            prepend="Converting file... "
        )
    for row in reader:
        if args.exclude_silent and row['Variant_Classification'] == 'Silent':
            continue
        if args.v:
            bar.update(i)
        i += 1
        if not args.skip_keyfile:
            row["Key"] = "%s_%d" % (row["Chromosome"], i)
        row["Chromosome"] = "chr"+row["Chromosome"]
        row["Start_position"] = int(row["Start_position"])
        row["End_position"] = int(row["End_position"])
        if (row["Variant_Classification"].endswith("_Ins")):
            if row["Start_position"] != row["End_position"]:
                row["End_position"] -= 1
        else:
            row["Start_position"] -= 1
        if not args.skip_keyfile:
            keyWriter.writerow({key: row[key] for key in keyWriter.fieldnames})
        writer.writerow({key: row[key] for key in writer.fieldnames})
    args.output.close()
    args.input.close()
    if not args.skip_keyfile:
        key_file.close()
    if args.v:
        bar.clear(True)


def main(args_input=sys.argv[1:]):
    from pkg_resources import get_distribution
    parser = argparse.ArgumentParser("maf2bed")
    parser.add_argument(
        '--version',
        action='version',
        version="%(prog)s (agutil) verion "+get_distribution('agutil').version,
        help="Display the current version and exit"
    )
    subparsers = parser.add_subparsers()

    maf2bed_parser = subparsers.add_parser(
        "convert",
        help="Converts a .maf file to .bed"
    )
    maf2bed_parser.set_defaults(func=maf2bed)
    maf2bed_parser.add_argument(
        'input',
        type=argparse.FileType('r'),
        help="Input maf file to parse"
    )
    maf2bed_parser.add_argument(
        'output',
        type=argparse.FileType('w'),
        help="Output bed file"
    )
    maf2bed_parser.add_argument(
        '--exclude-silent',
        action='store_true',
        help="Ignore silent mutations"
    )
    maf2bed_parser.add_argument(
        '--skip-keyfile',
        action='store_true',
        help="Don't generate a keyfile.  The output will be a single file "
        "which is identical to the original maf, except coordinates have been "
        "0-indexed."
    )
    maf2bed_parser.add_argument(
        '-v',
        action='store_true',
        help="Show a progress indicator"
    )

    bedkey_parser = subparsers.add_parser(
        "lookup",
        help="Lookup a full .maf entry from a key"
    )
    bedkey_parser.set_defaults(func=bedkey)
    bedkey_parser.add_argument(
        "input",
        type=argparse.FileType('r'),
        help="Input .bed.key file"
    )
    bedkey_parser.add_argument(
        "keys",
        nargs="+",
        help="Keys to lookup"
    )
    bedkey_parser.add_argument(
        '--suppress',
        action='store_true',
        help="Suppress printing to stdout.  Return the keys instead (for "
        "using lookup within other python scripts)"
    )
    args = parser.parse_args(args_input)

    try:
        return args.func(args)
    except AttributeError:
        print("usage: maf2bed [-h] {convert,lookup} ...")
        print(
            "maf2bed: error: must provide a command",
            "(choose from 'convert', 'lookup')"
        )
        sys.exit(-1)


if __name__ == '__main__':
    main()
