#!/usr/bin/env python

import pandas as pd
from fuzzywuzzy import fuzz
from nltk.corpus import stopwords
import json
import re
from pprint import pprint
import string
import sys

exclude = set(string.punctuation)
include = set('.')
exclude -= include
cachedStopWords = set(stopwords.words("english"))

def handle_titles(x):
    """
    Helper function to make string all lowercase and remove punctuation & stopwords.

    x: any string
    """
    x = x.strip().lower()
    x = x.replace('/', ' ')  # replace '/' with space
    x = x.replace('-', ' ')  # replace '-' with space
    x = ''.join(ch for ch in x if ch not in exclude)
    x = ' '.join(word for word in x.split() if word not in cachedStopWords)
    return x.strip()

def handle_products(x):
    """
    pre-process text in product_name or model

    :param x:
    :return:
    """
    x = x.strip().lower()
    return re.sub(r'[\W_]', ' ', x).strip()  # replace '_' and all non-alphanumeric with ' '
                                     # x will only contain [a-z0-9] with ' '


def match_model(title, model):
    """
    Determine if model is reflected in title

    >>> match_model("sony cyber shot dsc w310", "dsc w310")
    MODEL-MATCH:EXACT
    >>> match_model("sony cyber shot dsc w310x", "dsc w310")
    NOTMATCH

    >>> match_model("sony cyber shot sx130is", "sx130 is")
    MODEL-MATCH:MODEL_NOSPACE
    >>> match_model("sony cyber shot usx130is", "sx130 is")
    NOTMATCH

    >>> match_model("sony cyber shot sx130 is", "sx130is")
    MODEL-MATCH:TITLE_NOSPACE
    >>> match_model("sony cyber shot usx130 is", "sx130is")
    NOTMATCH
    """

    if model in title:
        starts = [m.start() for m in re.finditer(model, title)]
        for si in starts:
            ei = si + len(model) - 1
            if si >= 1 and title[si-1] not in [' ']:
                return "NOTMATCH"
            if ei+1 <= len(title)-1 and title[ei+1] not in [' ']:
                return "NOTMATCH"
        return "MODEL-MATCH:EXACT"

    model_nospace = model.replace(" ", "")
    if model_nospace in title:
        starts = [m.start() for m in re.finditer(model_nospace, title)]
        for si in starts:
            ei = si + len(model_nospace) - 1
            if si >= 1 and title[si-1] not in [' ']:
                return "NOTMATCH"
            if ei+1 <= len(title)-1 and title[ei+1] not in [' ']:
                return "NOTMATCH"
        return "MODEL-MATCH:MODEL_NOSPACE"

    # strip all space from title too
    title_nospace = title.replace(" ", "")
    if model_nospace in title_nospace:
        # for title_nospace, find mapping to index in original string
        mapping = []
        tidx = 0
        for i, v in enumerate(title_nospace):
            while v != title[tidx]:
                tidx += 1
            mapping.append(tidx)
            tidx += 1
        assert(tidx == len(title))

        starts = [m.start() for m in re.finditer(model_nospace, title_nospace)]
        ends = [x+len(model_nospace)-1 for x in starts]
        # map starts/ends back to indexes in original title
        starts_orig = [mapping[i] for i in starts]
        ends_orig = [mapping[i] for i in ends]

        for si in starts_orig:
            if si >= 1 and title[si-1] not in [' ']:
                return "NOTMATCH"
        for ei in ends_orig:
            if ei+1 <= len(title)-1 and title[ei+1] not in [' ']:
                return "NOTMATCH"
        return "MODEL-MATCH:TITLE_NOSPACE"

    return "NOTMATCH"

def match_manufacturer(listing_manuf, product_manuf):
    """
    Determine if manufacture is a match

    >>> match_manufacturer("Olympus", "Olympus")
    MANUF-MATCH:EXACT
    >>> match_manufacturer("Canon Canada", "Canon")
    MANUF-MATCH:EXACT
    >>> match_manufacturer("Canon", "Canon Canada")
    MANUF-MATCH:EXACT
    >>> match_manufacturer("cam", "camera")
    MANUF-MATCH:EXACT
    >>> match_manufacturer("Samsung Electronics GmbH DSC Division", "Samsung")
    MANUF-MATCH:EXACT
    """

    if product_manuf in listing_manuf or listing_manuf in product_manuf:
        return "MANUF-MATCH:EXACT"

    return "NOTMATCH"


def experiment_match_model(title_raw, model_raw):
    title_neat = handle_titles(title_raw)
    model_neat = handle_products(model_raw)
    print(title_raw + '\n' + title_neat)
    print(model_raw + '\n' + model_neat)
    print(match_model(title_neat, model_neat))


def find_listings_with_matched_manufacturer(df_listings_sorted, product_manuf):
    """
    Binary search reduces time complexity from O(N) to O(logN), but at the cost of
    missing matching strings like the following:
    ("usa canon", "canon")
    Otherwise, use the plain search to find all that matches

    Assume that manufacturer (in products) is not empty string

    :param df_listings_sorted:
    :param product_manuf:
    :return: a list of index (of df_listings_sorted) in ascending order
    """

    listings_index = []
    start_idx = 0
    end_idx = len(df_listings_sorted) - 1
    mid_idx = (start_idx + end_idx) / 2

    while end_idx-start_idx > 1:
        mid_value = df_listings_sorted.iloc[mid_idx].manufacturer
        if match_manufacturer(mid_value, product_manuf) == "MANUF-MATCH:EXACT":
            listings_index.append(mid_idx)
            # expand from mid_idx in both directions
            i = 1
            while mid_idx-i >= 0:
                v = df_listings_sorted.iloc[mid_idx-i].manufacturer
                if match_manufacturer(v, product_manuf) == "MANUF-MATCH:EXACT":
                    listings_index.append(mid_idx-i)
                    i += 1
                else:
                    break
            i = 1
            while mid_idx+i <= len(df_listings_sorted)-1:
                v = df_listings_sorted.iloc[mid_idx+i].manufacturer
                if match_manufacturer(v, product_manuf) == "MANUF-MATCH:EXACT":
                    listings_index.append(mid_idx+i)
                    i += 1
                else:
                    break
            break
        elif mid_value < product_manuf:
            start_idx = mid_idx
            mid_idx = (start_idx + end_idx) / 2
        elif mid_value > product_manuf:
            end_idx = mid_idx
            mid_idx = (start_idx + end_idx) / 2

    return sorted(listings_index)


def purge_model(model, title, match_result):
    if match_result == "MODEL-MATCH:EXACT":
        return title.replace(model, "")


def match_product(product, df_listings_sorted):

    # 1st time match based on "manufacturer"
    list_idx_1stmatch = find_listings_with_matched_manufacturer\
        (df_listings_sorted, product.manufacturer)

    # DEBUG
    # list_idx_1stmatch = find_listings_with_matched_manufacturer\
    #     (df_listings_sorted, "vtechnology")

    # Relate to index in original listings
    original_list_idx_1stmatch = []
    for idx in list_idx_1stmatch:
        original_list_idx_1stmatch.append(df_listings_sorted.iloc[idx].name)

    # combine index_of_empty_manufacturers and indexes of matched manufacturer
    original_list_idx_1stmatch = original_index_of_empty_manufacturers + original_list_idx_1stmatch
    list_idx_1stmatch = index_of_empty_manufacturers + list_idx_1stmatch

    #print(original_list_idx_1stmatch)
    #print(list_idx_1stmatch)


    # 2nd time match based on "model"
    for idx in list_idx_1stmatch:
        match_result = match_model(df_listings_sorted.iloc[idx].title, product.model)
        purge_model(product.model, df_listings_sorted.iloc[idx].title, match_result)
        purge_model(product.model, product_name)





if __name__ == '__main__':
    #title = "Olympus PEN E-PL1 12.3MP Live MOS Micro Four Thirds Interchangeable Lens Digital Camera with 14-42mm f/3.5-5.6 Zuiko Digital Zoom Lens (Black)"
    #model = "Olympus_PEN_E-PL1"
    #experiment_match_model(title, model)

    #print(match_manufacturer("Olympus", "Olympus"))
    #print(match_manufacturer("Canon Canada", "Canon"))
    #print(match_manufacturer("Canon", "Canon Canada"))

    products = []
    listings = []
    with open('data/products.txt') as products_file:
        for line in products_file:
            products.append(json.loads(line))
    with open('data/listings.txt') as listings_file:
        for line in listings_file:
            listings.append(json.loads(line))
    df_products = pd.DataFrame(products, columns=['product_name', 'manufacturer', 'family', 'model'])
    df_listings = pd.DataFrame(listings, columns=['title', 'manufacturer', 'price', 'currency'])
    df_products = df_products.fillna('')

    df_products['product_name'] = df_products.product_name.apply(handle_products)
    df_products['manufacturer'] = df_products.manufacturer.apply(handle_products)
    df_products['model'] = df_products.model.apply(handle_products)
    df_listings['title'] = df_listings.title.apply(handle_titles)
    df_listings['manufacturer'] = df_listings.manufacturer.apply(handle_products)

    df_listings = df_listings.sort_values('manufacturer', axis=0)  # sorted by manufacturer

    original_index_of_empty_manufacturers = []
    index_of_empty_manufacturers = []
    i = 0
    for index, row in df_listings.iterrows():
        if not row['manufacturer']:
            original_index_of_empty_manufacturers.append(index)
            index_of_empty_manufacturers.append(i)
            i += 1
        else:
            break
    #print(index_of_empty_manufacturers)

    for prod_idx, prod_row in df_products.iterrows():
        match_product(prod_row, df_listings)
        sys.exit(1)