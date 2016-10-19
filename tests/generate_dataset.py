#!/usr/bin/python
from random import randint
import json
from datetime import timedelta
from datetime import date
import random
import calendar
import sys

# Quantity of records
if len(sys.argv) > 1:
	N = pow(2,int(sys.argv[1]))
else:
	N = pow(2,6)

print "Generating a dataset with %d records" % N

# seed
firstnames = (['Tanner','Leland','Noble','Elroy','Irvin','Monty','Michael','Kristopher','Gonzalo','Elmo','Britt','Demarcus','Joey','Russ','Ismael','Dale','Santos','Melvin','Clifford','Cedrick','Jamel','Gustavo','Duncan','Wyatt','Otha','Kim','Lane','Trinidad','Kareem','Marcos','Edwardo','Cristopher','Jeramy','Willis','Ronnie','Maxwell','Carmelo','Rudy','Ulysses','Norbert','Isreal','Andreas','Odell','Heath','Palmer','Brenton','Whitney','Herman','Clinton','Alphonso'])
surnames = (['Alves','Tallman','Wiechmann','Newcomb','Leatherwood','Teneyck','Dworkin','Bloomfield','Weinberger','Holtman','Li','Ruder','Asuncion','Holden','Haug','Bonfiglio','Hayles','Roseborough','Bensen','Maliszewski','Durgin','Mitten','Mcfall','Greenidge','Nowakowski','Au','Malcolm','Dail','Warthen','Schubert','Ballantine','Depaul','Roa','Figueredo','Dotson','Marrow','Cusic','Dalpiaz','Geddie','Graham','Mark','Hymel','Laroque','Chapple','Pasek','Rustin','Burg','Romo','Burnham','Runge','Hawkes','Lindgren','Aller','Carcamo','Winzer','Heishman','Mayne','Carmona','Villagomez','Biondi','Waterfield','Metzger','Kary','Bates','Benesh','Pleasant','Vong','Correira','Demoura','Gelinas','Alejos','Hulin','Sayegh','Hinkson','Wofford','Musselman','Mora','Dipiazza','Cliff','Barnhardt','Issa','Paula','Winkler','Lawhead','Murray','Scism','Cartagena','Oconner','Hermsen','Doten','Goldstein','Hites','Faivre','Hern','Grana','Lietz','Kawamura','Heard','Shaver','Tostado','Begum','Berthelot','Bakken','Bumgardner','Shroyer','Onstad','Martensen','Mcfall','Boling','Weil','Saur','Rubinstein','Visitacion','Concepcion','Claire','Ostlund','Augsburger','Gravley','Gao','Nixon','Espada','Malta','Dunkerson','Leija','Brimmer','Ozment','Opie','Olivarez','Raleigh','Marietta','Noss','Braz','Cribbs','Crooms','Merkley','Greenwood','Begay','Saban','Alcocer','Cerezo','Grasso','Kulpa','Mcneal','Heideman','Stong','Krogh','Giampaolo','Hullett','Belue','Bhatia','Brust'])
countries = (['Afghanistan','Albania','Algeria','American Samoa','Andorra','Angola','Anguilla','Antarctica','Antigua And Barbuda','Argentina','Armenia','Aruba','Australia','Austria','Azerbaijan','Bahamas','Bahrain','Bangladesh','Barbados','Belarus','Belgium','Belize','Benin','Bermuda','Bhutan','Bolivia','Bosnia And Herzegovina','Botswana','Bouvet Island','Brazil','British Indian Ocean Territory','Brunei Darussalam','Bulgaria','Burkina Faso','Burundi','Cambodia','Cameroon','Canada','Cape Verde','Cayman Islands','Central African Republic','Chad','Chile','China','Christmas Island','Cocos (keeling) Islands','Colombia','Comoros','Congo','Congo, The Democratic Republic Of The','Cook Islands','Costa Rica','Cote Divoire','Croatia','Cuba','Cyprus','Czech Republic','Denmark','Djibouti','Dominica','Dominican Republic','East Timor','Ecuador','Egypt','El Salvador','Equatorial Guinea','Eritrea','Estonia','Ethiopia','Falkland Islands (malvinas)','Faroe Islands','Fiji','Finland','France','French Guiana','French Polynesia','French Southern Territories','Gabon','Gambia','Georgia','Germany','Ghana','Gibraltar','Greece','Greenland','Grenada','Guadeloupe','Guam','Guatemala','Guinea','Guinea-bissau','Guyana','Haiti','Heard Island And Mcdonald Islands','Holy See (vatican City State)','Honduras','Hong Kong','Hungary','Iceland','India','Indonesia','Iran, Islamic Republic Of','Iraq','Ireland','Israel','Italy','Jamaica','Japan','Jordan','Kazakstan','Kenya','Kiribati','Korea, Democratic Peoples Republic Of Korea, Republic Of','Kosovo','Kuwait','Kyrgyzstan','Lao Peoples Democratic Republic','Latvia','Lebanon','Lesotho','Liberia','Libyan Arab Jamahiriya','Liechtenstein','Lithuania','Luxembourg','Macau','Macedonia, The Former Yugoslav Republic Of','Madagascar','Malawi','Malaysia','Maldives','Mali','Malta','Marshall Islands','Martinique','Mauritania','Mauritius','Mayotte','Mexico','Micronesia, Federated States Of','Moldova, Republic Of','Monaco','Mongolia','Montserrat','Montenegro','Morocco','Mozambique','Myanmar','Namibia','Nauru','Nepal','Netherlands','Netherlands Antilles','New Caledonia','New Zealand','Nicaragua','Niger','Nigeria','Niue','Norfolk Island','Northern Mariana Islands','Norway','Oman','Pakistan','Palau','Palestinian Territory, Occupied','Panama','Papua New Guinea','Paraguay','Peru','Philippines','Pitcairn','Poland','Portugal','Puerto Rico','Qatar','Reunion','Romania','Russian Federation','Rwanda','Saint Helena','Saint Kitts And Nevis','Saint Lucia','Saint Pierre And Miquelon','Saint Vincent And The Grenadines','Samoa','San Marino','Sao Tome And Principe','Saudi Arabia','Senegal','Serbia','Seychelles','Sierra Leone','Singapore','Slovakia','Slovenia','Solomon Islands','Somalia','South Africa','South Georgia And The South Sandwich Islands','Spain','Sri Lanka','Sudan','Suriname','Svalbard And Jan Mayen','Swaziland','Sweden','Switzerland','Syrian Arab Republic','Taiwan, Province Of China','Tajikistan','Tanzania, United Republic Of','Thailand','Togo','Tokelau','Tonga','Trinidad And Tobago','Tunisia','Turkey','Turkmenistan','Turks And Caicos Islands','Tuvalu','Uganda','Ukraine','United Arab Emirates','United Kingdom','United States','United States Minor Outlying Islands','Uruguay','Uzbekistan','Vanuatu','Venezuela','Viet Nam','Virgin Islands, British','Virgin Islands, U.s.','Wallis And Futuna','Western Sahara','Yemen','Zambia','Zimbabwe'])

# data model
# this object is not really necessary
model = { 'domain':None,
		  'name':None,
		  'expires_on':None,
		  'registered_on':None,
		  'updated_on':None,
		  'name_servers':None,
		  'accesses':None
		}


# Assuming you want a random day of the current year
firstJan = date.today().replace(day=1, month=1) 


# creates an empty dataset
dataset = []
for i in xrange(N):
	# clones
	print i

	record = dict(model)
	fn = firstnames[randint(0,len(firstnames)-1)]
	sn = surnames[randint(0,len(surnames)-1)]
	expires_on = firstJan + timedelta(days = random.randint(0, 365 if calendar.isleap(firstJan.year) else 364))

	record["accesses"] = 0
	record["name"] = fn+sn
	record["domain"] =  "www."+fn+"-"+sn+".com.br"
	record["expires_on"] = expires_on.toordinal()
	record["updated_on"] = (expires_on + timedelta(days = randint(0, 365 if calendar.isleap(firstJan.year) else 364))).toordinal()
	record["registered_on"] = (expires_on - timedelta(days = randint(0, 365 if calendar.isleap(firstJan.year) else 364))).toordinal()
	record["name_servers"] = "%d.%d.%d.%d" % (randint(192,202),randint(0,100),randint(0,100),randint(0,100))

	dataset.append(record)

output = open("synthetic_dataset_%d.json"%N,"w+")
json.dump(dataset,output)