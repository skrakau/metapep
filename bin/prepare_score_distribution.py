#!/usr/bin/env python3
#
# Author: Sabrina Krakau
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
####################################################################################################

import argparse
import sys
import os
import csv

import pandas as pd

####################################################################################################

def parse_args(args=None):
    """Parses the command line arguments specified by the user."""
    parser = argparse.ArgumentParser(description="Prepare prediction score distribution for plotting.")

    # INPUT FILES
    parser.add_argument("-p"     , "--predictions"              , help="Path to the predictions input file"                     , type=str   , required=True)
    parser.add_argument("-ppo"   , "--protein-peptide-occ"      , help="Path to the protein peptide occurences input file"      , type=str   , required=True)
    parser.add_argument("-epo"   , "--entities-proteins-occ"    , help="Path to the entity protein occurences input file"       , type=str   , required=True)
    parser.add_argument("-meo"   , "--microbiomes-entities-occ" , help="Path to the microbiome entity occurences input file"    , type=str   , required=True)
    parser.add_argument("-c"     , "--conditions"               , help="Path to the conditions input file"                      , type=str   , required=True)
    parser.add_argument("-cam"   , "--condition-allele-map"     , help="Path to the condition allele map input file"            , type=str   , required=True)
    parser.add_argument("-a"     , "--alleles"                  , help="Path to the allele input file"                          , type=str   , required=True)

    # OUTPUT FILES
    parser.add_argument("-o"     , "--outdir"                   , help="Path to the output directory"                           , type=str   , required=True)

    # PARAMETERS
    return parser.parse_args()



def main(args=None):
    args = parse_args(args)

    # Read input files
    predictions               = pd.read_csv(args.predictions, sep='\t')
    protein_peptide_occs      = pd.read_csv(args.protein_peptide_occ, sep='\t').drop(columns="count")
    entities_proteins_occs    = pd.read_csv(args.entities_proteins_occ, sep='\t')
    microbiomes_entities_occs = pd.read_csv(args.microbiomes_entities_occ, sep='\t')
    conditions                = pd.read_csv(args.conditions, sep='\t')
    condition_allele_map      = pd.read_csv(args.condition_allele_map, sep='\t')
    alleles                   = pd.read_csv(args.alleles, sep='\t')

    # Create output directory if it doesn't exist
    if os.path.exists(args.outdir) and not os.path.isdir(args.outdir):
        print("ERROR - The target path is not a directory", file = sys.stderr)
        sys.exit(2)
    elif not os.path.exists(args.outdir):
        os.makedirs(args.outdir)

    print("Joining input data...", file = sys.stderr, flush=True, end='')

    # for each allele separately (to save mem)
    for allele_id in alleles.allele_id:
        print("Process allele: ", allele_id, flush=True)

        data = predictions[predictions.allele_id == allele_id] \
                .merge(protein_peptide_occs) \
                .merge(entities_proteins_occs) \
                .drop(columns="protein_id") \
                .merge(microbiomes_entities_occs) \
                .drop(columns="entity_id") \
                .merge(conditions) \
                .merge(condition_allele_map) \
                .drop(columns=["allele_id", "microbiome_id", "condition_id"]) \
                .groupby(["peptide_id", "prediction_score", "condition_name"])["entity_weight"] \
                .sum() \
                .reset_index(name="weight_sum") \
                .drop(columns="peptide_id")
        # NOTE
        # for each peptide in a condition the weight is computed as follows:
        # - the sum of all weights of the corresponding entity_weights, each weighted by the number of proteins in which the peptide occurs
        # - multiple occurrences of the peptide within one protein are not counted

        with open(os.path.join(args.outdir, "prediction_scores.allele_" + str(allele_id) + ".tsv"), 'w') as outfile:
            data[["prediction_score", "condition_name", "weight_sum"]].to_csv(outfile, sep="\t", index=False, header=True)

        for condition_name in data.condition_name.drop_duplicates():
            print("Wrote out ", len(data[data.condition_name == condition_name]), " prediction scores for condition_name ", condition_name, ".", flush=True)


if __name__ == "__main__":
    sys.exit(main())
