import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import json
import os

# import stopwords
stopwords = []
with open("stopwords.txt", 'r') as file:
    for line in file:
        stopwords.append(line.strip('\n'))

global_links = []
global_frequencies = {}
frequenciesfile = 'frequencies.json'
linksfile = 'links.json'


def tokenize(content):
    tokens = re.findall(r'[a-z]+', content.lower())
    return tokens


def wordfreq(tokenlist, tokenmap):
    for v in tokenlist:
        if v not in tokenmap.keys():
            tokenmap[v] = 1
        else:
            tokenmap[v] = tokenmap[v] + 1


def printfreq(frequencies):
    sorted_frequencies = sorted(
        frequencies.items(), key=lambda item: (-item[1], item[0].lower()))
    limit = 0
    for token, count in sorted_frequencies:
        if limit == 50:
            break
        elif token not in stopwords:
            limit += 1
            print(f"{limit}: {token} = {count}")
        else:
            continue


def save_to_json(frequencies, filename):
    data = {}
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            data = json.load(file)

    for token, count in frequencies.items():
        if token not in stopwords:
            if token in data.keys():
                data[token] = data[token] + count
            elif not token in data.keys():
                data[token] = count

    sorteddata = {k: v for k, v in sorted(
        data.items(), key=lambda item: item[1], reverse=True)}
    with open(filename, 'w') as file:
        json.dump(sorteddata, file)


def load_links(filename):
    data = []
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            data = json.load(file)
    return data


def save_links(links, filename):
    with open(filename, 'w') as file:
        json.dump(links, file)


def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]


def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    # return list()

    if not is_valid(url):  # check if valid url first
        return []
    elif resp.status != 200:  # check status 200
        return []
    else:
        if url not in global_links:
            global_links.append(url)
        # parse using beautifulsoup
        soup = BeautifulSoup(resp.raw_response.content, "lxml")
        links = soup.find_all("a")  # find all hyperlinks

        text = soup.get_text()
        tokened = tokenize(text)  # tokened the html content
        wordfreq(tokened, global_frequencies)
        save_to_json(global_frequencies, 'frequencies.json')

        extracted_links = []
        for link in links:
            href = link.get("href")  # pull out only the raw link in text form
            if href and is_uci(href):  # check to see if its a uci link
                if link not in global_links:
                    # it it is, append it to the extracted links
                    extracted_links.append(href)
                    global_links.append(href)  # add to links gone through
        return extracted_links


def is_valid(url):
    # Decide whether to crawl this url or not.
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False

        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print("TypeError for ", parsed)
        raise


def is_uci(url):
    # a copy of the is_valid function but with the inclusion of checking if it is an ics.uci.edu link
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False

        if not parsed.netloc.endswith("ics.uci.edu"):
            return False

        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print("TypeError for ", parsed)
        raise


# testing the parsing
if __name__ == "__main__":
    # at first i thought a dictionary would suffice but it wouldn't work
    # so i resorted to utilizing class inside class to allow for attributes
    class ResponseMain:
        class raw_response:
            def __init__(self, url, content):
                self.url = url
                self.content = content

        def __init__(self, url, status, content):
            self.url = url
            self.status = status
            self.raw_response = self.raw_response(url, content)

    url = "https://example.com"
    status = 200
    raw_response_content = "<html><body><a href='https://example.com/page1'>Link 1</a><a href='https://example.com/page2'>Link 2</a><a href='https://example.ics.uci.edu/page3'>Link 3</a></body></html>"
    resp = ResponseMain(url, status, raw_response_content)
    extracted_links = extract_next_links(url, resp)

    # print out the links that do work
    print("Extracted links:")
    for link in extracted_links:
        print(link)
