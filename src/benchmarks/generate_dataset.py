#!/usr/bin/python
#coding: utf-8
###########################################################################
##########################################################################
#
# mongodb-secure
# Copyright (C) 2016, Pedro Alves and Diego Aranha
# {pedro.alves, dfaranha}@ic.unicamp.br

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
##########################################################################
##########################################################################
# This routine generates a random dataset. This has elements that symbolize a 
# contact list.
#
# A parameter may be passed specifying the quantity of elements in the dataset.
# Otherwise this number will be set to 10^4/2.
#

from random import randint,shuffle
import loremipsum
import json
import sys

outputfilename = "synthetic_dataset.json"

# Quantity of entries

if len(sys.argv) > 1:
	N = int(sys.argv[1])
else:
	N = pow(10,4)/2

ages = range(0,N)
# seed
male_firstnames = (['Tanner','Leland','Noble','Elroy','Irvin','Monty','Michael','Kristopher','Gonzalo','Elmo','Britt','Demarcus','Joey','Russ','Ismael','Dale','Santos','Melvin','Clifford','Cedrick','Jamel','Gustavo','Duncan','Wyatt','Otha','Kim','Lane','Trinidad','Kareem','Marcos','Edwardo','Cristopher','Jeramy','Willis','Ronnie','Maxwell','Carmelo','Rudy','Ulysses','Norbert','Isreal','Andreas','Odell','Heath','Palmer','Brenton','Whitney','Herman','Clinton','Alphonso'])
female_firstnames = (['Colette','Kayleen','Suellen','Serena','Linsey','Aline','Carry','Pearlene','Merlyn','Cindy','Tanja','Elvie','Yung','Lahoma','Kayce','Taryn','Eufemia','Karyn','Chantelle','Indira','Katerine','Hue','Margeret','Ila','Beaulah','Selene','Ora','Krystal','Jeana','Devorah','Adele','Amberly','Susannah','Johna','Danica','Dulce','Kami','Janiece','Cleotilde','Venita','Shenika','Sharyn','Patrica','Gilma','Ivey','Fidela','Anamaria','Londa','Pearline','Elfriede'])
surnames = (['Alves','Tallman','Wiechmann','Newcomb','Leatherwood','Teneyck','Dworkin','Bloomfield','Weinberger','Holtman','Li','Ruder','Asuncion','Holden','Haug','Bonfiglio','Hayles','Roseborough','Bensen','Maliszewski','Durgin','Mitten','Mcfall','Greenidge','Nowakowski','Au','Malcolm','Dail','Warthen','Schubert','Ballantine','Depaul','Roa','Figueredo','Dotson','Marrow','Cusic','Dalpiaz','Geddie','Graham','Mark','Hymel','Laroque','Chapple','Pasek','Rustin','Burg','Romo','Burnham','Runge','Hawkes','Lindgren','Aller','Carcamo','Winzer','Heishman','Mayne','Carmona','Villagomez','Biondi','Waterfield','Metzger','Kary','Bates','Benesh','Pleasant','Vong','Correira','Demoura','Gelinas','Alejos','Hulin','Sayegh','Hinkson','Wofford','Musselman','Mora','Dipiazza','Cliff','Barnhardt','Issa','Paula','Winkler','Lawhead','Murray','Scism','Cartagena','Oconner','Hermsen','Doten','Goldstein','Hites','Faivre','Hern','Grana','Lietz','Kawamura','Heard','Shaver','Tostado','Begum','Berthelot','Bakken','Bumgardner','Shroyer','Onstad','Martensen','Mcfall','Boling','Weil','Saur','Rubinstein','Visitacion','Concepcion','Claire','Ostlund','Augsburger','Gravley','Gao','Nixon','Espada','Malta','Dunkerson','Leija','Brimmer','Ozment','Opie','Olivarez','Raleigh','Marietta','Noss','Braz','Cribbs','Crooms','Merkley','Greenwood','Begay','Saban','Alcocer','Cerezo','Grasso','Kulpa','Mcneal','Heideman','Stong','Krogh','Giampaolo','Hullett','Belue','Bhatia','Brust'])
countries = (['Afghanistan','Albania','Algeria','American Samoa','Andorra','Angola','Anguilla','Antarctica','Antigua And Barbuda','Argentina','Armenia','Aruba','Australia','Austria','Azerbaijan','Bahamas','Bahrain','Bangladesh','Barbados','Belarus','Belgium','Belize','Benin','Bermuda','Bhutan','Bolivia','Bosnia And Herzegovina','Botswana','Bouvet Island','Brazil','British Indian Ocean Territory','Brunei Darussalam','Bulgaria','Burkina Faso','Burundi','Cambodia','Cameroon','Canada','Cape Verde','Cayman Islands','Central African Republic','Chad','Chile','China','Christmas Island','Cocos (keeling) Islands','Colombia','Comoros','Congo','Congo, The Democratic Republic Of The','Cook Islands','Costa Rica','Cote Divoire','Croatia','Cuba','Cyprus','Czech Republic','Denmark','Djibouti','Dominica','Dominican Republic','East Timor','Ecuador','Egypt','El Salvador','Equatorial Guinea','Eritrea','Estonia','Ethiopia','Falkland Islands (malvinas)','Faroe Islands','Fiji','Finland','France','French Guiana','French Polynesia','French Southern Territories','Gabon','Gambia','Georgia','Germany','Ghana','Gibraltar','Greece','Greenland','Grenada','Guadeloupe','Guam','Guatemala','Guinea','Guinea-bissau','Guyana','Haiti','Heard Island And Mcdonald Islands','Holy See (vatican City State)','Honduras','Hong Kong','Hungary','Iceland','India','Indonesia','Iran, Islamic Republic Of','Iraq','Ireland','Israel','Italy','Jamaica','Japan','Jordan','Kazakstan','Kenya','Kiribati','Korea, Democratic Peoples Republic Of Korea, Republic Of','Kosovo','Kuwait','Kyrgyzstan','Lao Peoples Democratic Republic','Latvia','Lebanon','Lesotho','Liberia','Libyan Arab Jamahiriya','Liechtenstein','Lithuania','Luxembourg','Macau','Macedonia, The Former Yugoslav Republic Of','Madagascar','Malawi','Malaysia','Maldives','Mali','Malta','Marshall Islands','Martinique','Mauritania','Mauritius','Mayotte','Mexico','Micronesia, Federated States Of','Moldova, Republic Of','Monaco','Mongolia','Montserrat','Montenegro','Morocco','Mozambique','Myanmar','Namibia','Nauru','Nepal','Netherlands','Netherlands Antilles','New Caledonia','New Zealand','Nicaragua','Niger','Nigeria','Niue','Norfolk Island','Northern Mariana Islands','Norway','Oman','Pakistan','Palau','Palestinian Territory, Occupied','Panama','Papua New Guinea','Paraguay','Peru','Philippines','Pitcairn','Poland','Portugal','Puerto Rico','Qatar','Reunion','Romania','Russian Federation','Rwanda','Saint Helena','Saint Kitts And Nevis','Saint Lucia','Saint Pierre And Miquelon','Saint Vincent And The Grenadines','Samoa','San Marino','Sao Tome And Principe','Saudi Arabia','Senegal','Serbia','Seychelles','Sierra Leone','Singapore','Slovakia','Slovenia','Solomon Islands','Somalia','South Africa','South Georgia And The South Sandwich Islands','Spain','Sri Lanka','Sudan','Suriname','Svalbard And Jan Mayen','Swaziland','Sweden','Switzerland','Syrian Arab Republic','Taiwan, Province Of China','Tajikistan','Tanzania, United Republic Of','Thailand','Togo','Tokelau','Tonga','Trinidad And Tobago','Tunisia','Turkey','Turkmenistan','Turks And Caicos Islands','Tuvalu','Uganda','Ukraine','United Arab Emirates','United Kingdom','United States','United States Minor Outlying Islands','Uruguay','Uzbekistan','Vanuatu','Venezuela','Viet Nam','Virgin Islands, British','Virgin Islands, U.s.','Wallis And Futuna','Western Sahara','Yemen','Zambia','Zimbabwe'])

# data model
# this object is not really necessary
model = { 'email':None,
		   'firstname':None,
		   'surname':None,
		   'country':None,
		   'age':None,
		   'text':None
		}


# creates an empty dataset
print "Generating a dataset with %d elements..." % N,
shuffle(ages)
dataset = []
for i in xrange(N):
	# clones
	#print i

	record = dict(model)

	record["age"] = max((ages[i]+1) % 50,1) # 
	record["country"] = countries[randint(0,len(countries)-1)]
	record["surname"] = surnames[randint(0,len(surnames)-1)]
	record["text"] = "".join(loremipsum.get_paragraphs(randint(1,2)))

	gender = randint(0,1)
	if gender is 1:
		#male
		record["firstname"] = male_firstnames[randint(0,len(male_firstnames)-1)]
	else:
		#female
		record["firstname"] = female_firstnames[randint(0,len(female_firstnames)-1)]

	record["email"] =  record["firstname"]+"."+record["surname"]+"@something.com"

	dataset.append(record)

output = open(outputfilename,"w+")
json.dump(dataset,output)

print "Done."
print "Saved to %s" % outputfilename