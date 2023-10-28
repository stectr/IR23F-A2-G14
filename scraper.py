import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import json
import os
import robotexclusionrulesparser
import xml.etree.ElementTree as ET


# import stopwords
stopwords = []
with open("stopwords.txt", 'r') as file:
    for line in file:
        stopwords.append(line.strip('\n'))

# global_links = []
global_frequencies = {}
frequenciesfile = 'frequencies.json'
linksfile = 'links.json'
counter = 0


def tokenize(content):
    tokens = re.findall(r'[a-z]+', content.lower())
    return tokens


def wordfreq(tokenlist, tokenmap):
    for v in tokenlist:
        if v not in stopwords:
            if v not in tokenmap.keys():
                tokenmap[v] = 1
            else:
                tokenmap[v] = tokenmap[v] + 1
                

def uniqueTokens(tokenlist):
    freq = {}
    for v in tokenlist:
        if v not in stopwords:
            if v not in freq.keys():
                freq[v] = 1
            else:
                freq[v] = freq[v] + 1
                
    return freq.length()


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


def load_frequencies(filename):
    data = {}
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            data = json.load(file)
    return data


def save_frequencies(frequencies, filename):
    data = {}
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
    global counter
    global global_frequencies
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
    elif resp.status < 200 or resp.status > 399:  # check status 200
        return []
    elif is_large_file(url, resp):
        return []
    # elif not check_robots(url):
    #     return []
    else:
          # Fetch sitemap and return links from sitemap if available
        # parsed_url = urlparse(url)
        # sitemap_url = f"{parsed_url.scheme}://{parsed_url.netloc}/sitemap.xml"
        # sitemap_links = fetch_sitemap(sitemap_url, resp)
        # if sitemap_links:
        #     return sitemap_links
        
        # parse using beautifulsoup
        soup = BeautifulSoup(resp.raw_response.content, "lxml")
        links = soup.find_all("a")  # find all hyperlinks

        text = soup.get_text()
        tokened = tokenize(text)  # tokenize the text

        global_links = load_links("links.json")
        if counter == 0:
            global_frequencies = load_frequencies("frequencies.json")

        if resp.raw_response.url not in global_links:
            #     global_links.append(url)
            # add tokens to global_frequencies
            
            # if uniqueToken(tokened) > 30:
            global_links.append(resp.raw_response.url)  # add link to links visited
            save_links(global_links, "links.json")
            
            wordfreq(tokened, global_frequencies)
            counter += 1
            if counter == 200:
                save_frequencies(global_frequencies, "frequencies.json")
                counter = 0

        # the meat of extracting next set of links
        extracted_links = []
        for link in links:
            href = link.get("href")  # pull out only the raw link in text form
            if href and is_uci(href):  # check to see if its a uci link
                if link not in global_links:
                    # it it is, append it to the extracted links
                    extracted_links.append(href)
                    # global_links.append(href)  # add to links gone through

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
    except ValueError as e:
        print(f"Error parsing URL {url}: {e}")
        return False  # Return False or handle the error in some other way
    
    try:
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

def check_robots(url):
    parsed_url = urlparse(url)
    robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
    robots_parser = robotexclusionrulesparser.RobotFileParserLookalike()
    try:
        robots_parser.url = robots_url
        robots_parser.read()
        return robots_parser.is_allowed("*", url)
    except:
        return True  # Allow crawling if robots.txt is unreachable or improperly formatted
    
def is_large_file(url, resp, size_threshold=10*1024*1024, token_threshold=100):
    """
    Check if a file is large and contains a low count of tokenized data.
    
    :param url: The URL of the file.
    :param resp: The response object.
    :param size_threshold: The file size threshold (default is 10 MB).
    :param token_threshold: The token count threshold (default is 100).
    :return: True if the file is large and has a low token count, False otherwise.
    """
    if resp.status == 200:
        # Check file size
        content_length = int(resp.raw_response.headers.get('Content-Length', 0))
        is_large_file = content_length > size_threshold
        
        # Tokenize the content
        content = resp.raw_response.content.decode('utf-8', errors='ignore')
        tokens = tokenize(content)
        token_count = len(tokens)
        has_low_token_count = token_count < token_threshold
        # print(f"Failed to parse XML from {url}")
        
        if is_large_file and has_low_token_count:
            print("File was large with low content")

        return is_large_file and has_low_token_count

    return False


def fetch_sitemap(url, resp):
    try:
        # Attempt to parse the XML content
        root = ET.fromstring(resp.raw_response.content)
    except ET.ParseError as e:
        # Log the error and the location of the error in the XML
        print(f"XML Parse Error at {e.position}: {e.msg}")
        print(f"Failed to parse XML from {url}")
        return []

    # Check if this is a sitemap index
    if root.tag == '{http://www.sitemaps.org/schemas/sitemap/0.9}sitemapindex':

        print("there is an xml!")
        # It's a sitemap index, so fetch and parse the sitemaps listed in the index
        sitemap_links = []
        for sitemap in root.findall('{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap'):
            loc = sitemap.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
            if loc is not None:
                sitemap_url = loc.text
                sitemap_resp = fetch_url(sitemap_url)  # Use your function instead of requests.get
                if sitemap_resp.status == 200:
                    sitemap_root = ET.fromstring(sitemap_resp.raw_response.content)
                    sitemap_links.extend([child.text for child in sitemap_root.iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')])
                else:
                    print(f"Failed to fetch sitemap from {sitemap_url}")
        return sitemap_links
    else:
        # It's a regular sitemap, so extract and return the URLs
        return [child.text for child in root.iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]


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
    
    
    
    # Test check_robots function
    robots_test_url = "https://www.ics.uci.edu"
    print(f"Robots.txt check for {robots_test_url}: {check_robots(robots_test_url)}")

    # Test fetch_sitemap function
    sitemap_test_url = "https://www.ics.uci.edu/sitemap.xml"
    # Create a dummy response object for sitemap_test_url
    dummy_resp = ResponseMain(sitemap_test_url, 200, "<xml></xml>")  # assuming the content is not important for this test
    sitemap_links = fetch_sitemap(sitemap_test_url, dummy_resp)
    print(f"Sitemap links for {sitemap_test_url}: {sitemap_links}")
