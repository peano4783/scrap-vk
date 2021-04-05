## Scraping social media for analyzing errors in writingpping

We collected a dataset that was used by linguists to analyze frequent error patterns in Russian social media.
I scrapped text messages from popular Russian social network VK.com using VK API, then split the messages down to single words,
got the words to the main form (singular masculine for adjectives, infinitive for verbs etc.) and sought this form in the dictionary:
in case the word was absent from the dictionary, the word was marked as "suspicious for error".
