### Doing it

* checks for invalid social media link before display
* Make it so that candidates committees are in tab for ‘current term’ 
* Make it so that candidate committees are clickable
* (maybe) setup docker for project (what do we gain)

### Thinking about it


| Bug Fixes     | Ideas            | Other People    |  Graphical Things
| -------------|-------------|-----------------|-----------------|
| Dynamic placement / scrolling of boxes*  | Possibly also get social media things for state reps?  | HTML5 ASTEROIDS while you wait Jessi talk to Mikey? | how to display title (State House/Senate/House of Representatives) | 
| | how to differentiate between state vs. country level | talk to Audry about site | | 
| Separate bills into larger categories(or do wordcloud?) | Add actionables for contact information (using countable possibly?)_%_  | talk to Ryan about site design |
| Start writing tests | Add SSL (add nginx container to dockerfile)
| Too long of text, limit text by box | Display total money raised somewhere on rep tile
| Don't think python -m flask run is right way to deploy | How to make website faster+ 
| | 
| | possibly make historical searches more accessible?
             
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