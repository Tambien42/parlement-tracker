import scrapy

class ScrutinsanSpider(scrapy.Spider):
    name = 'scrutinsAN'
    allowed_domains = ['assemblee-nationale.fr']
    start_urls = ['https://www2.assemblee-nationale.fr/scrutins/liste/(legislature)/16/']

    def non_votant(self, response):
        non_votant = 0
        div = response.css('div.Non-votant')

        for d in div:
            try:
                i = response.css('div.Non-votant p b ::text').get()
                non_votant = non_votant + int(i)
            except ValueError:
                pass
        
        # Follow the link to the previous page
        prev_page_url = response.meta['prev_page']
        yield scrapy.Request(prev_page_url, callback=self.parse)
        
        # Yield the extracted data as an item
        yield {'non_votant': non_votant}

    def parse(self, response):
        # Extract the rows from the table
        rows = response.xpath('//table[@class="scrutins"]/tbody/tr')

        # Iterate over the rows
        for row in rows:
            # Extract the number, date, and object of the vote
            number = row.xpath('./td[1]/text()').extract_first()
            date = row.xpath('./td[2]/text()').extract_first()
            object = row.xpath('./td[3]/text()').extract_first()

            # Extract the number of votes for, against, and abstention
            votes_for = row.xpath('./td[4]/text()').extract_first()
            votes_against = row.xpath('./td[5]/text()').extract_first()
            votes_abstention = row.xpath('./td[6]/text()').extract_first()

            # Extract the number of Non Votant
            url_analyse_scrutin = row.xpath('./td[3]/a/@href')[-1].get()
            u = 'https://www2.assemblee-nationale.fr' + url_analyse_scrutin
            yield scrapy.Request(response.urljoin(u), callback=self.non_votant, meta={'prev_page': response.url})

            # Yield the extracted data as an item
            yield {
                'number': number,
                'date': date,
                'object': object,
                'votes_for': votes_for,
                'votes_against': votes_against,
                'votes_abstention': votes_abstention
            }


        # Check if there is a next page
        next = response.css('div.pagination-bootstrap li:last-child a::attr(href)').get()
        
        if next:
            # If there is a next page, follow the link and scrape it
            next_page_url  = 'https://www2.assemblee-nationale.fr' + next
            yield scrapy.Request(response.urljoin(next_page_url), self.parse)
