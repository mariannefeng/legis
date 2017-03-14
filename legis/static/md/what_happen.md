### Doing it

* Change bill info to be displayed using D3
* Make it so that candidate committees are clickable
* (maybe) setup docker for project (what do we gain: easy SSL)
* Multiple bill download 
* Login for Edit Mode
### Thinking about it


| Bug Fixes     | Ideas            | Other People    |  Graphical Things
| -------------|-------------|-----------------|-----------------|
| Dynamic placement / scrolling of boxes*  | Possibly also get social media things for state reps?  | HTML5 ASTEROIDS while you wait Jessi talk to Mikey? | how to display title (State House/Senate/House of Representatives) | 
| What the fuck is going on with the encoding | how to differentiate between state vs. country level | | | 
| Separate bills into larger categories(or do wordcloud?) | Add actionables for contact information (using countable possibly?)_%_  | talk to Ryan about site design |
| Start writing tests (definitely need something that checks to make sure dependencies are still up) | Add SSL (add nginx container to dockerfile)
| Too long of text, limit text by box | Display total money raised somewhere on rep tile
| Don't think python -m flask run is right way to deploy -- We might want to look into Heroku for app deployment I don't know much about it but bitches love it.| How to make website faster+
|Change Form to JSON so testing isn't as annoying| Consider possibility of making this thing local?
| | possibly make historical searches more accessible?
| | If you can't load picture for X from A source, maybe try B source? 
| | Any way to add Balletopedia API? -- I think we have to pay for it, but it would be worth it. 
| | Here's a crazy thought - what if you also got information on things that impact your LIFE (school board, public works, tranpo, housing...)
| | Add mock data so we don't have to wait for shit when working on css changes
| | Make it so that you can click on tabs in 'Extra Credit' and pull for old committee info
| | Add on hover tip for information you're looking at - there's that one git glossary repo! 
| | Starting thinking about doing data...cleansing service. There's a better word for it. You know what I'm talking about. 

             
+Have requests cache, but need metrics
*so if the screen is small the contact info/committees/social media info doesn’t dwarf the picture and make the tile huge
_%_might render social media links useless

*Markdown page TODOS*: 
  * add basic password
  * make both left + right side shrink based on page width
  * maybe possibly make markdown edit page tab toggle?
  * add text diff check before sending (_right now sends every 15 seconds_)
  * add notification for 2 users being connected at once
  * make it so editor box is same height as other column
  * show markdown tips somewhere?


### Done it

~~Retrieve financial data for country level people - MARIANNE~~
~~what to do about empty bills? --JESSI~~
~~might be good to show state member historical roles since…some are….blank. Good to know they’re new or some shit? - JESSI~~
~~Simple requests cache - JESSI~~
~~make all the pictures the same size - MARIANNE~~
~~Display committees for country level reps~~
~~show social media buttons and link to them MARIANNE~~
~~add default for no picture - MARIANNE~~
~~Make homepage sexy - JESSI~~
~~Validate homepage form - JESSI~~
~~Display pretty graph for financial data for country level people MARIANNE~~
~~Make all boxes fixed height~~
~~Fix financial data bug (look at what happens for Arizon~~
~~We need a page to list our sources (gasp what if you make it markdown)~~
~~checks for invalid social media link before display~~
~~Make it so that candidates committees are in tab for 'current term'~~