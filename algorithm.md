# Algorithim

```
assuming we have paragraphs tagged with maxent quote model:

	identify paragraphs with quotes

	for key, paragraph in enumerate(positively_identified_paragraphs):

		#########################################
		####### curent paragraph features #######
		#########################################
		if nonquote_section has word "said":
			'''
			<QUOTE> said Jorge Costa, the Giants operations director. 
			'''
			return PERSON(S) immediately before or after "said"
		
		elif nonquote_section has {<VBD|VBZ><DT>?<NN|NNP|NNS>+|<DT>?<NN|NNP|NNS>+<VBD|VBZ>}:
			'''
			On Jan. 26, The Bay Citizen filed a public records request for <QUOTE>
			'''
			return return <DT>?<NN|NNP|NNS>+ or <NN|NNP|NNS>+<DT>?
		
		elif nonquote_section has <PERSON><,><.*><,*><VBD|VBZ>:
			'''Ex.
			McDevitt, who has three teenage sons and an 11-year-old daughter, said <QUOTE>
			'''
			return PERSON nearest to quote_paragraph
		
		elif nonquote_section has PERSON:
			'''Ex.
			<QUOTE>, said 22-year-old Vanna Ruiz, of Morgan Hill.
			San Francisco Police Chief Greg Suhr would only say that <QUOTE>
			'''
			return PERSON nearest to word "said" or <VBD|VBZ>

		###########################################
		####### previous paragraph features #######
		###########################################
		elif last sentence has "said" in positively_identified_paragraphs[key-1]:
			return PERSON nearest to quote_paragraph

		elif last sentence has {<PERSON><VBD|VBZ>|<VBD|VBZ><PERSON>} in positively_identified_paragraphs[key-1]:
			return PERSON nearest to quote_paragraph
			
		elif last sentence has {<VBD|VBZ><DT>?<NN|NNP|NNS>+|<DT>?<NN|NNP|NNS>+<VBD|VBZ>} in positively_identified_paragraphs[key-1]:
			return <DT>?<NN|NNP|NNS>+ or <NN|NNP|NNS>+<DT>?

		elif last sentence has <PERSON><,><.*><,*><VBD|VBZ> in positively_identified_paragraphs[key-1]:
			return PERSON nearest to quote_paragraph

		elif last sentence has <PERSON> in positively_identified_paragraphs[key-1]:
			return PERSON nearest to quote_paragraph

		elif <PERSON> "said" in positively_identified_paragraphs[key-2]:
			'''Ex.
			Farming allows soldiers to decompress, Colin Archipley said. \
			For him, the benefits of growing food are tangible. <QUOTE>
			'''
			return <PERSON>

		############################################
		####### preceding paragraph features #######
		############################################
		elif first sentence has "said" in positively_identified_paragraphs[key+1]:
			return PERSON nearest to quote_paragraph

		elif first sentence has {<PERSON><VBD|VBZ>|<VBD|VBZ><PERSON>} in positively_identified_paragraphs[key+1]:
			return PERSON nearest to quote_paragraph

		elif first sentence has {<VBD|VBZ><NN|NNP|NNS>+|<NN|NNP|NNS>+<VBD|VBZ>} in positively_identified_paragraphs[key+1]:
			return <NN|NNP|NNS> nearest to quote_paragraph

		elif first sentence has <PERSON><,><.*><,*><VBD|VBZ> in positively_identified_paragraphs[key+1]:
			return PERSON nearest to quote_paragraph

		elif first sentence has <PERSON> in positively_identified_paragraphs[key+1]:
			return PERSON nearest to quote_paragraph

		#########################
		####### fall back #######
		#########################
		else:
			most common <PERSON> in document
```