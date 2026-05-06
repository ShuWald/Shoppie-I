# Logic

## [High Priority] Risk Assessment Logic
\- Tariff, supply, competition functionality not integrated (Frontend uses fake values)
    \- Tariffs seems ready to integrate
    \- Shelf-life can also be used, LLM choice for estimation questionable
\- FDA approval only checks product description, ingredients fetching not implemented

## [High Priority] Data Source Integration
\- Tariffs API 
\- Ingredients scraper important for fixing fda assessment logic
\- They seem like they're ready, but they're all standalone files...
\- Also see [[## [High Priority] Error Handling]]

## [High Priority] Error Handling
\- Most important, no gaurdrails/error handling for missing or inconsistent scraping/API data
\- Scoring should also adjust missing values

## [Medium-High Priority (imo)] Code Clarity
\- Very easy to implement, but very impactful
\- Comments indicating every instance of fake/placeholder data or functionality. Please. 
\- Organization
    \- Directories to logically separate files

## [Low Priority] Trends Webscraper 
\- Update main trends_data CSV file
\- Useful for scalability as well
\- Trigger condition? Backend startup will be good for now

## [Low Priority] Sorting
\- Create and maintain sorted CSV versions of main file
    \- Not optimal with current caching implementation
\- Triggered on `intialize` (on backend startup)


# Frontend
\- Rounding floating-point issue
\- "alignswith" and more missing spaces in full report feature
\- The entire trends page is missing real functionality
\- Refresh analysis button currently provides no real value
\- Header bar / Interactive UI improvements?
\- Fixed sidebar takes up space
\- Market Growth vs Consumer Interest Graph off-screen
\- Scores by Product graph struggles with higher numbers of products


# Expansion / Improvements
\- Implement Postgres or other database tool instead of using CSVs
\- Search functionality
\- (ambitious/time-consuming) Data analysis for user selected items?
\- UI / Accessibility / Interactivity
    \- Dark Mode Toggle
    \- Appealing color palette
    \- More interactive items
    \- Optimized layout

# Other