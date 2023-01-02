import scrapy


class ScrutinsanSpider(scrapy.Spider):
    name = 'scrutinsAN'
    allowed_domains = ['https://www2.assemblee-nationale.fr/']
    start_urls = ['http://https://www2.assemblee-nationale.fr/scrutins/liste/(legislature)/16/']

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

            # Print the extracted data
            print(f'Number: {number}, Date: {date}, Object: {object}, Votes for: {votes_for}, Votes against: {votes_against}, Votes abstention: {votes_abstention}')

            # Check if there is a next page
            next_page_url = response.css('div.pagination-bootstrap li:last-child a::attr(href)').get()
            if next_page_url:
                # If there is a next page, follow the link and scrape it
                yield scrapy.Request(response.urljoin(next_page_url), self.parse)
