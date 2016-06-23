import argparse
import csv
import re

def main():
    parser = argparse.ArgumentParser("tsvManip")
    parser.add_argument(
        'input',
        type=argparse.FileType('r'),
        help="Input .tsv file to be parsed"
    )
    parser.add_argument(
        'output',
        type=argparse.FileType('w'),
        help="Output file"
    )
    parser.add_argument(
        '--no-headers',
        action='store_true',
        help="Flag indicating that there are is no header row"
    )
    parser.add_argument(
        '-c', '--col',
        action='append',
        type=int,
        help="Column containing input data to parse (0-indexed). " +
            "Multiple columns can be selected by providing the option multiple times " +
            "(Ex: --col 0 --col 5 --col 6).  All columns are selected by default",
        dest="cols",
        metavar="COLUMN",
        default=[]
    )
    parser.add_argument(
        '-d', '--delim',
        action="append",
        help="Delimiters for splitting input columns into multiple new columns for output "+
            "Delimiters can be specified for multiple columns by providing the option multiple times " +
            "Delimiters are matched to colums by order provided.  For example, " +
            "the first delimiter provided matches to the first column parsed for input. " +
            "An underscore (_) indicates no delimiter for that column. " +
            "To use a delimiter consisting entirely of one or more underscores, " +
            "append a single underscore to the end of the delimiter string. " +
            "(Ex: '--delim __' (two underscores) indicates a delimiter of '_' (one underscore) ). "
            "Multiple delimiters can be provided for the same column by prefixing " +
            "the delimiters for the string with <column #>:\n" +
            "Delimiters for the same column are applied in the order provided " +
            "to all resulting columns from subsequent splits. " +
            "Prefixed delimiter inputs will not affect the matching of unprefixed delimiters to columns. " +
            "(Ex: --col 0 --col 1 --delim <used for col 0> --delim <used for col 1>)\n" +
            "(Ex: --col 1 --col 4 --delim <used for col 1> --delim <used for col 4> --delim 1:<used for col 1>)",
        dest="delims",
        metavar="DELIMITER",
        default=[]
    )
    parser.add_argument(
        '--i0',
        action='append',
        type=int,
        help="Selected columns should be shifted from 1 to 0 index. "+
        "This is applied after selected columns are plucked from the input, and split by delimiters. "+
        "Provided column numbers match the indecies of columns after those steps. " +
        "Multiple columns can be selected by supplying the argument multiple times",
        metavar="COL",
        default=[]
    )
    parser.add_argument(
        '-s', '--strip-commas',
        type=int,
        action='append',
        help="Strip commas from the specified columns.  Column numbers reference before mapping, but after splitting",
        default=[],
        metavar="COL"
    )
    parser.add_argument(
        '-m', '--map',
        action='append',
        help="Mappings to map plucked columns to output columns. " +
        "Use to change the order of columns.  Maps are in the format of: " +
        "<input column #>:<output column #>\n" +
        "This is the last step in parsing, so input column #'s should be relative " +
        "to any changes made by plucking and splitting",
        metavar="IN:OUT",
        default=[],
        dest='maps'
    )
    parser.add_argument(
        '-v',
        action='store_true',
        help="Provide verbose output"
    )
    args = parser.parse_args()

    if len(args.cols) == 0:
        tmp_reader = open(args.input.name, mode='r')
        intake = tmp_reader.readline()
        args.cols = list(range(len(intake.split("\t"))))

    mappings = [[int(item) for item in mapping.split(":")] for mapping in args.maps]

    col_prefix_matcher = re.compile(r"\d+:")
    underscore_only = re.compile(r'_*$')
    delims = [delim for delim in args.delims if not col_prefix_matcher.match(delim)]
    delims = {args.cols[i]:[delims[i]] for i in range(len(delims)) if delims[i]!="_"}
    for delim in args.delims:
        if col_prefix_matcher.match(delim):
            tmp = delim.split(":")
            index = int(tmp[0])
            parsed = ":".join(tmp[1:])
            if index in delims:
                delims[index].append(parsed)
            else:
                delims[index]=[parsed]
    for i in delims:
        delims[i] = [
            delim[1:] if underscore_only.match(delim) else delim for delim
                in delims[i]
        ]
    if args.v:
        print("Delimiters:",delims)
    reader = csv.reader(args.input, delimiter='\t')
    writer = csv.writer(args.output, delimiter='\t', lineterminator='\n')

    if not args.no_headers:
        header = next(reader)

    args.cols = set(args.cols)
    args.i0 = set(args.i0)
    args.strip_commas = set(args.strip_commas)
    for row in reader:
        filtered = {i:[row[i]] for i in range(len(row)) if i in args.cols}
        for i in filtered:
            if i in delims:
                for delim in delims[i]:
                    filtered[i] = [
                        subitem for item in filtered[i] for subitem in item.split(delim)
                    ]
        split = [subitem for item in filtered.values() for subitem in item]

        reindexed = [
            "{:,}".format(int(split[i].replace(',',''))-1) if i in args.i0 else split[i]
                for i in range(len(split))
        ]

        finalized = [
            reindexed[i].replace(",","") if i in args.strip_commas else reindexed[i]
                for i in range(len(reindexed))
        ]

        for mapping in mappings:
            tmp = finalized.pop(mapping[0])
            finalized = finalized[:mapping[1]] + [tmp] + finalized[mapping[1]:]
        if args.v:
            print("Finalized row:", finalized)
        writer.writerow(finalized)
    args.input.close()
    args.output.close()



if __name__ == '__main__':
    main()
