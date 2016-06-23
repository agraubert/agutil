import argparse
from subprocess import call
import sys
import csv

def bedkey(args):
    args.keys = set(args.keys)
    reader = csv.DictReader(args.input, delimiter='\t')

    for row in reader:
        if row['Key'] in args.keys:
            print(row)

    args.input.close()

def maf2bed(args):
    if args.v and sys.platform=="win32":
        print("Maf2bed does not yet support this feature on windows")
        args.v = False
    if args.v:
        from subprocess import run, PIPE
        args.v = int(run(['wc -l %s'%args.input.name], shell=True, stdout=PIPE).stdout.decode().split()[0])
    key_file = None
    if not args.skip_keyfile:
        key_file = open(args.output.name+".key", mode='w')
    reader = csv.DictReader(args.input, delimiter='\t')
    keyWriter = None
    writer_fields = reader.fieldnames if args.skip_keyfile else ["Chromosome", "Start_position", "End_position", "Key"]
    if not args.skip_keyfile:
        keyWriter = csv.DictWriter(key_file, ["Key"] + reader.fieldnames, delimiter='\t', lineterminator='\n')
    writer = csv.DictWriter(args.output, writer_fields, delimiter='\t', lineterminator='\n')

    keyWriter.writeheader()
    i = 0
    bar = None
    if args.v:
        from ..status_bar import status_bar
        bar = status_bar(args.v, show_percent=True)
    for row in reader:
        if args.exclude_silent and row['Variant_Classification'] == 'Silent':
            continue
        bar.update(i)
        i+=1
        if not args.skip_keyfile:
            row["Key"] = "%s_%d" %(row["Chromosome"], i)
        row["Chromosome"] = "chr"+row["Chromosome"]
        row["Start_position"] = int(row["Start_position"])
        row["End_position"] = int(row["End_position"])
        if (row["Variant_Classification"].endswith("_Ins")):
            if row["Start_position"] != row["End_position"]:
                row["End_position"] -= 1
        else:
            row["Start_position"] -= 1
        keyWriter.writerow({key:row[key] for key in keyWriter.fieldnames})
        writer.writerow({key:row[key] for key in writer.fieldnames})
    args.output.close()
    bar.clear(True)

def main():
    parser = argparse.ArgumentParser("maf2bed")
    subparsers = parser.add_subparsers()

    maf2bed_parser = subparsers.add_parser("convert", help="Converts a .maf file to .bed")
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
        help="Don't generate a keyfile.  The output will be a single file which is identical to the original maf, except coordinates have been 0-indexed."
    )
    maf2bed_parser.add_argument(
        '-v',
        action='store_true',
        help="Show a progress indicator"
    )

    bedkey_parser = subparsers.add_parser("lookup", help="Lookup a full .maf entry from a key")
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
    args = parser.parse_args()

    args.func(args)





if __name__ == '__main__':
    main()
