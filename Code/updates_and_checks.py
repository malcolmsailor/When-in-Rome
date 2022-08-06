# -*- coding: utf-8 -*-
"""
===============================
Updates and Checks (updates_and_checks.py)
===============================

Mark Gotham, 2020-


LICENCE:
===============================

Creative Commons Attribution-ShareAlike 4.0 International License
https://creativecommons.org/licenses/by-sa/4.0/


ABOUT:
===============================

Functions for updating entries to the 'When in Rome' corpus of harmonic analyses, notably:
- copying, moving, converting scores and analyses;
- creating 'slices' and 'template' files (from the score)
- producing 'feedback' and 'analysis_on_score' files (from a score and analysis pair)
- various checks.

See also 'contents.py' for updating corpus contents lists.

"""

# ------------------------------------------------------------------------------

import json
import os
import shutil

from typing import Optional, Union

import romanUmpire

from music21 import converter, stream


# ------------------------------------------------------------------------------

corpora = [
    'Orchestral',
    'Early_Choral',
    'Etudes_and_Preludes',
    'OpenScore-LiederCorpus',
    'Piano_Sonatas',
    'Quartets',
    'Variations_and_Grounds'
]


# ------------------------------------------------------------------------------

def get_corpus_files(corpus: str = 'OpenScore-LiederCorpus',
                     file_name: Optional[str] = '',
                     name_end: Optional[str] = ''
                     ) -> list:
    '''
    Get and return paths to files matching conditions for either
    the whole file name (file_name) or only the end (extension or otherwise).
    If the entire file name is specified, end is ignored.
    :param corpus: the sub-corpus to search over. Empty string ('') to run all corpora.
    :param file_name: a full file name (optional)
    :param name_end: the end of the file name (file extension or otherwise, optional)
    :return: list of file paths.
    '''

    if corpus != '' and corpus not in corpora:
        raise ValueError(f"Invalid corpus: must be one of {corpora} or an empty string (for all)")

    base_path = os.path.join(os.path.dirname((os.path.realpath(__file__))), '..', 'Corpus', corpus)

    paths = []

    for dpath, dname, fname in os.walk(base_path):
        for name in fname:
            if file_name:
                if name == file_name:
                    paths.append(str(os.path.join(dpath, name)))
            elif name_end:  # ignored if search on whole file name
                if name.endswith(name_end):
                    paths.append(str(os.path.join(dpath, name)))

    return paths


def get_analyses(corpus: str = 'OpenScore-LiederCorpus',
                 all_versions: bool = True
                 ) -> list:
    """
    Get analysis files across a corpus.
    (I.e., Convenience function for `get_corpus_files` on analyses.)

    :param corpus:
    :param all_versions: If True, get all analysis files ('analysis*txt'); if false, only get the
    'analysis.txt' files.
    :return: list of file paths.
    """

    f = 'analysis.txt'
    if all_versions:
        f = 'analysis*txt'
    return get_corpus_files(corpus=corpus, file_name=f)


# ------------------------------------------------------------------------------

# Roman Umpire

def process_one_score(path_to_score: str,
                      path_to_analysis,  # NB 'On Score' option
                      write_path: str,
                      combine: bool = True,
                      slices: bool = True,
                      feedback: bool = True,
                      overwrite: bool = False):
    """
    Processes one score to produce any or all of the following files:
    'analysis_on_score' (score files with analysis added in musical notation),
    'slices_with_analysis' (tsv representation that's a valid input for the Roman umpire and
    quicker to parse than musicXML), and
    'feedback' (txt written feedback on the score-analysis match).

    :param path_to_score:
    :param path_to_analysis: a string as path, or simply 'On score' *** (see romanUmpire).
    :param write_path: where to write any new files to.
    :param combine: create an `analysis_on_score` file with the two combined.
    :param slices: create a 'slices.tsv' representation.
    :param feedback: produce feedback on how the analysis matches the score (write to .txt)
    :param overwrite: if False and the file type already exists, don't replace it.
    """

    if (not combine) and (not slices) and (not feedback):
        print('No action requested: set at least one of combine, slices, or feedback to true.')
        return

    t = romanUmpire.ScoreAndAnalysis(path_to_score,
                                     analysisLocation=path_to_analysis)

    stopping_message = 'file exists and overwrite set to False. Stopping'

    if combine:
        if overwrite:
            t.writeScoreWithAnalysis(outPath=write_path,
                                     outFile='analysis_on_score')
        else:
            hypothetical_path = os.path.join(path_to_score, 'analysis_on_score.mxl')
            if os.path.exists(hypothetical_path):
                print('analysis_on_score ' + stopping_message)
            else:
                t.writeScoreWithAnalysis(outPath=write_path,
                                         outFile='analysis_on_score')

    if slices:
        t.matchUp()  # Sic, necessary here and only here
        if overwrite:
            t.writeSlicesFromScore(outPath=write_path,
                                   outFile='slices_with_analysis')
        else:
            hypothetical_path = os.path.join(path_to_score, 'slices_with_analysis.tsv')
            if os.path.exists(hypothetical_path):
                print('slices_with_analysis ' + stopping_message)
            else:
                t.writeSlicesFromScore(outPath=write_path,
                                       outFile='slices_with_analysis')

    if feedback:
        if overwrite:
            t.printFeedback(outPath=write_path,
                            outFile='feedback_on_analysis')
        else:
            hypothetical_path = os.path.join(path_to_score, 'feedback_on_analysis.txt')
            if os.path.exists(hypothetical_path):
                print('feedback_on_analysis ' + stopping_message)
            else:
                t.printFeedback(outPath=write_path,
                                outFile='feedback_on_analysis')


def process_corpus(corpus: str = 'OpenScore-LiederCorpus',
                   combine: bool = True,
                   slices: bool = True,
                   feedback: bool = True,
                   overwrite: bool = False):
    """
    Corpus wide implementation of `process_one_score`. See docs there.
    """
    files = get_corpus_files(corpus=corpus,
                             file_name='analysis.txt')

    for path_to_analysis in files:
        pth = path_to_analysis[:-len("analysis.txt")]
        print(pth)
        analysis_exist = os.path.exists(pth + "analysis_on_score.mxl")
        if overwrite or (not analysis_exist):
            try:
                process_one_score(os.path.join(pth, 'score.mxl'),
                                  path_to_analysis,  # i.e. with 'analysis'
                                  pth,
                                  combine=combine,
                                  slices=slices,
                                  feedback=feedback)
            except:
                print(f'Error with: {pth}')


# ------------------------------------------------------------------------------

# Scores

def convert_musescore_score_corpus(in_path: Union[str, os.PathLike],
                                   out_path: Union[str, os.PathLike],
                                   corpus_name: str = 'mozart_piano_sonatas',
                                   in_format: str = '.mscx',
                                   out_format: str = '.mxl',
                                   write: bool = True,
                                   ) -> list:
    """
    Basic script for creating or updating a
    `<corpus_name>_corpus_conversion.json` file with 
    the latest contents of the corpus so that it can be used 
    for batch conversion of 
    musescore files (mscx or mscz) 
    to mxl or other fileformat.

    Specifically, set up to map from DCML conventions 
    e.g., in the mozart_piano_sonatas from `/K279-1.mscx` into 
    local convention for subfolders `/K279/1/score.mxl`.

    Implement the batch conversion of one such file
    e.g., `corpus_conversion.json`
    from this folder with the command:
    >>> mscore -j corpus_conversion.json

    For information about `mscore` and a within-app plugin alternative, see
    https://musescore.org/en/handbook/3/command-line-options#Run_a_batch_job_converting_multiple_documents

    Possible TODO:
    Consider running directly from URL (i.e., not a local copy), e.g., ...
    https://raw.githubusercontent.com/DCMLab/mozart_piano_sonatas/main/scores/K279-1.mscx
    ... though this doesn't seem to be supported by mscore.    
    """

    valid_formats = ['.mscx', '.mscz', '.mxl', '.pdf', '.mid']
    if in_format not in valid_formats:
        raise ValueError(f"Invalid in_format: must be one of {valid_formats}")
    if out_format not in valid_formats:
        raise ValueError(f"Invalid out_format: must be one of {valid_formats}")

    valid_corpora = ['ABC', 'mozart_piano_sonatas']
    if corpus_name not in valid_corpora:
        raise ValueError(f"Invalid in_format: must be one of {valid_corpora}")

    out_data = []

    for f in os.listdir(in_path):
        if f.endswith(in_format):
            if corpus_name == 'ABC':
                g = f.split('op')[1]  # n01op18-1_01.mscx >>> 18-1_01.mscx
                g = g.split('.')[0]  # 18-1_01.mscx >>> 18-1_01
                cln, mvt = g.split('_')  # 18-1_01 >>> 18-1, 01
                mvt = mvt[1]  # Remove DCML padding '01' >>> '1'. Never 10+ mvts
                no = ''
                if '-' in cln:  # Only if applicable. 18-1 >>> 18, 1
                    cln, no = cln.split('-')
                    no = 'No' + no  # No1
                if len(cln) == 2:  # 18, 59 etc.
                    cln = '0' + cln  # Add padding. Op100+ in collection.
                cln = 'Op' + cln
                if no:
                    cln = '_'.join([cln, no])  # Op018_No1
                mvt = mvt.split('.')[0]  # e.g.,  1.mcsx >>> 1
                # Op18_No1
            elif corpus_name == 'mozart_piano_sonatas':
                cln, mvt = f.split('-')  # e.g., K279-1.mscx >>> K279, 1.mcsx
                mvt = mvt.split('.')[0]  # e.g.,  1.mcsx >>> 1

            # if not isdir, mkdir
            cln_path = os.path.join(out_path, cln)
            if not os.path.isdir(cln_path):
                os.mkdir(cln_path)
            mvt_path = os.path.join(cln_path, mvt)
            if not os.path.isdir(mvt_path):
                os.mkdir(mvt_path)

            x = {'in': in_path + f,
                 'out': str(mvt_path) + '/score' + out_format
                 }

            out_data.append(x)

    if write:
        out_path = os.path.join('.', corpus_name + '_corpus_conversion.json')
        with open(out_path, 'w') as json_file:
            json.dump(out_data, json_file)

    return out_data


def copy_DCML_tsv_analysis_files(in_path: Union[str, os.PathLike],
                                 out_path: Union[str, os.PathLike],
                                 corpus_name: str = 'mozart_piano_sonatas',
                                 ) -> None:
    """
    Copy DCML's analysis files (.tsv) to the relevant
    `working` folder of this repo.
    
    TODO: DRY - refactor with `convert_musescore_score_corpus`
    """

    valid_corpora = ['ABC', 'mozart_piano_sonatas']
    if corpus_name not in valid_corpora:
        raise ValueError(f"Invalid in_format: must be one of {valid_corpora}")

    out_data = []

    for f in os.listdir(in_path):
        if f.endswith('.tsv'):
            if corpus_name == 'ABC':
                g = f.split('op')[1]  # n01op18-1_01.mscx >>> 18-1_01.mscx
                g = g.split('.')[0]  # 18-1_01.mscx >>> 18-1_01
                cln, mvt = g.split('_')  # 18-1_01 >>> 18-1, 01
                mvt = mvt[1]  # Remove DCML padding '01' >>> '1'. Never 10+ mvts
                no = ''
                if '-' in cln:  # Only if applicable. 18-1 >>> 18, 1
                    cln, no = cln.split('-')
                    no = 'No' + no  # No1
                if len(cln) == 2:  # 18, 59 etc.
                    cln = '0' + cln  # Add padding. Op100+ in collection.
                cln = 'Op' + cln
                if no:
                    cln = '_'.join([cln, no])  # Op018_No1
                mvt = mvt.split('.')[0]  # e.g.,  1.mcsx >>> 1
                # Op18_No1
            elif corpus_name == 'mozart_piano_sonatas':
                cln, mvt = f.split('-')  # e.g., K279-1.mscx >>> K279, 1.mcsx
                mvt = mvt.split('.')[0]  # e.g.,  1.mcsx >>> 1

            # if not isdir, mkdir
            cln_path = os.path.join(out_path, cln)
            if not os.path.isdir(cln_path):
                os.mkdir(cln_path)
            mvt_path = os.path.join(cln_path, mvt)
            if not os.path.isdir(mvt_path):
                os.mkdir(mvt_path)
            working_path = os.path.join(mvt_path, 'Working')
            if not os.path.isdir(working_path):
                os.mkdir(working_path)

            shutil.copy(in_path + f,
                        str(working_path) + '/DCML_analysis.tsv'
                        )


# ------------------------------------------------------------------------------

# Checks

def anacrusis_number_error(p: stream.Part
                           ) -> bool:
    '''
    Check whether anacrustic measures are numbered correctly in a part.
    If the first measure is incomplete (not equal in length to that of the stated time signature)
    then it should be numbered 0; if complete, it should be 1.

    NB:
    - There are known false positives for certain cases like crossing staves (missing events)
    - Multiple voices are untested.

    :param p: a music21.stream.Part, pre-parsed.
    :return: bool, True in the case of an error.
    '''
    msrs = p.getElementsByClass('Measure')
    m = msrs[0]

    if m.measureNumber == 0 and m.duration == m.barDuration:
        return True
    elif m.measureNumber == 1 and m.duration != m.barDuration:
        return True


def check_all_analyses_parse(corpus: str = 'OpenScore-LiederCorpus',
                             count_files: bool = True,
                             count_rns: bool = True
                             ) -> None:
    """
    Check all analysis files parse successful
    (throws and error on the first analysis to fail if not).
    Optionally count the number of analysis files and Roman Numerals therein.

    :param corpus: the sub-corpus to search over. Leave blank ('') to run all corpora.
    :param count_files: count+print the total number of analysis files (bool, optional).
    :param count_rns: count+print the total Roman numerals in all analysis files (bool, optional).
    """

    files = get_analyses(corpus=corpus)
    if count_files:
        print(f'{len(files)} analyses found ... now checking they all parse ...')

    rns = 0

    for f in files:
        a = converter.parse(f, format='romantext')
        if count_rns:
            rns += len(a.getElementsByClass('RomanNumeral'))

    print('All analyses parse')

    if count_rns:
        print(f'{rns} total Roman Numerals.')


def find_incomplete_measures(part: stream.Part
                             ) -> str:
    '''
    Finds cases of 'incomplete' measures as defined by a difference between the
    actual length of events in a measure and the nominal (time signature defined) length.

    False positives in cases like crossing staves (missing events)
    Untested: multiple voices. TODO: extract voice 1? Or forget parts and work directly on scores?

    :param part: a music21.stream.Part, pre-parsed
    :return: string with incomplete measure + first and last overall (not necessarily incomplete)
    '''
    msrs = part.getElementsByClass('Measure')
    first = msrs[0].measureNumber
    last = msrs[-1].measureNumber
    incomplete = []
    for m in msrs:
        if m.duration != m.barDuration:  # i.e. actual length differs from nominal (ts) length
            incomplete.append(m.measureNumber)

    return f'Incomplete: {incomplete}; first: {first}; last {last}'


def find_incomplete_measures_corpus(corpus: str = 'OpenScore-LiederCorpus',
                                    anacrusis_only: bool = True
                                    ) -> dict:
    """
    Run `anacrusis_number_error` or `find_incomplete_measures` on a whole corpus.
    :param corpus: the corpus to search (see get_corpus_files)
    :param anacrusis_only: bool. If True, only consider the first measure
    (i.e., run `anacrusis_number_error`), otherwise run `find_incomplete_measures`.
    :return: dict with file names as the keys.
    """

    # NB: corpus validity check in get_corpus_files
    files = get_corpus_files(corpus=corpus, file_name='score.mxl')
    out_dict = {}
    for file in files:
        print(f'Test: {file}')
        try:
            score = converter.parse(file)
            if anacrusis_only:
                out_dict[file] = anacrusis_number_error(score.parts[0])
            else:
                out_dict[file] = find_incomplete_measures(score.parts[0])
        except:
            print(f'Failed to parse {file}')

    if anacrusis_only:
        titles = [x for x in out_dict if out_dict[x]]
        titles.sort()
        print('ISSUES WITH:')
        [print(x) for x in titles]

    return out_dict

# ------------------------------------------------------------------------------