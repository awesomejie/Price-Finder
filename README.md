# Price-Finder
A project that matches product's price listings to the product

The project has its origin from the [Sortable's challenge](http://sortable.com/challenge/) 

Here is my Python solution. 

## Tested with environment
* Ubuntu 14.04 (64-bit)
* Python 2.7.11 
* pandas 0.17.1
* fuzzywuzzy 0.8.0 (installed via `pip install fuzzywuzzy`)
* nltk 3.1 (installed via `sudo pip install -U nltk`)

## How to test
Execute the command:
```
python main.py
```

Results are generated in file "outputs.txt". 

It took ~4min on my PC with 8-core and 16G memory for the program to finish matching with the current "listings.txt" and "products.txt".

To test on new data sets, replace "listings.txt" and "products.txt" in the data folder and run `python main.py`.