# API Schema

```json

{
	"route": "api",
	"paths": [
		{
			"path": "/menu/",
			"params": [
				{
					"key": "place",
					"type": "string",
					"help": "A restuarant id / slug",
					"required": true
				}	
			],
			"about": ""
		},
		{
			"path": "/menu/item/",
			"params": [
				{
					"key": "place",
					"type": "string",
					"help": "A restuarant id / slug",
					"required": true
				},
				{
					"key": "foodId",
					"type": "string",
					"help": "A food id",
					"required": true
				},
			],
			"about": ""
		},
		{
			"path": "/menu",
			"params": [
				{
					"key": "place",
					"type": "string",
					"help": "A restuarant id / slug",
					"required": false
				}	
			],
			"about": ""
		},
		{
			"path": "/menu",
			"params": [
				{
					"key": "place",
					"type": "string",
					"help": "A restuarant id / slug",
					"required": false
				}	
			],
			"about": ""
		},
	]
}

```