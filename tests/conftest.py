"""Synthetic Goodreads feeds shared by the test suite."""

SHELF_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Alex's bookshelf: currently-reading</title>
    <lastBuildDate>Tue, 15 Sep 2026 17:08:38 +0000</lastBuildDate>
    <item>
      <guid>https://www.goodreads.com/review/show/456?utm_source=rss</guid>
      <pubDate>Mon, 14 Sep 2026 17:00:58 +0000</pubDate>
      <title>Example Book</title>
      <link>https://www.goodreads.com/review/show/456?utm_source=rss</link>
      <book_id>123</book_id>
      <book_small_image_url>https://images.example/small.jpg</book_small_image_url>
      <book_medium_image_url>https://images.example/medium.jpg</book_medium_image_url>
      <book_large_image_url>https://images.example/large.jpg</book_large_image_url>
      <book><num_pages>320</num_pages></book>
      <author_name>Casey Writer</author_name>
      <isbn>1234567890</isbn>
      <user_name>Alex</user_name>
      <user_rating>0</user_rating>
      <user_read_at></user_read_at>
      <user_date_added>Mon, 14 Sep 2026 17:00:58 +0000</user_date_added>
      <user_date_created>Sun, 13 Sep 2026 10:00:00 +0000</user_date_created>
      <user_shelves>currently-reading, favourites</user_shelves>
      <average_rating>4.25</average_rating>
      <book_published>2026</book_published>
    </item>
  </channel>
</rss>
"""

UPDATES_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Alex's Updates</title>
    <item>
      <guid isPermaLink="false">UserStatus999</guid>
      <pubDate>Tue, 15 Sep 2026 17:08:38 +0000</pubDate>
      <description><![CDATA[
        <a href="/book/show/123-example-book">Alex</a>
        is on page 80 of 320 of &lt;a href="/book/show/123-example-book"&gt;Example Book&lt;/a&gt;.
      ]]></description>
    </item>
    <item>
      <guid isPermaLink="false">UserStatus998</guid>
      <pubDate>Mon, 14 Sep 2026 17:08:38 +0000</pubDate>
      <description><![CDATA[
        <a href="/book/show/123-example-book">Alex</a>
        is on page 40 of 320 of &lt;a href="/book/show/123-example-book"&gt;Example Book&lt;/a&gt;.
      ]]></description>
    </item>
    <item>
      <guid isPermaLink="false">ReadStatus777</guid>
      <pubDate>Mon, 14 Sep 2026 12:00:00 +0000</pubDate>
      <description><![CDATA[Alex started reading <a href="/book/show/789-another">Another</a>.]]></description>
    </item>
    <item>
      <guid isPermaLink="false">UserStatus666</guid>
      <pubDate>Sun, 13 Sep 2026 12:00:00 +0000</pubDate>
      <description><![CDATA[
        <a href="/book/show/789-another">Alex</a> is 42.5% done with Another.
      ]]></description>
    </item>
  </channel>
</rss>
"""
