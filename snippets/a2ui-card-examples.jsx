// The six example cards on interactions/custom-cards.mdx, as the exact
// message lists an agent sends. Each JSON block on that page is the same list.
export const A2uiCardExamples = () => ({
 "y2k": [
  {
   "version": "v1.0",
   "createSurface": {
    "surfaceId": "y2k",
    "catalogId": "https://relayapp.im/a2ui/catalogs/relay/v1/catalog.json"
   }
  },
  {
   "version": "v1.0",
   "updateComponents": {
    "surfaceId": "y2k",
    "components": [
     {
      "id": "root",
      "component": "StyledCard",
      "child": "col",
      "background": "#141832",
      "cornerRadius": 18
     },
     {
      "id": "col",
      "component": "Column",
      "children": [
       "header",
       "title",
       "body",
       "body2",
       "line",
       "divider",
       "footer",
       "cta"
      ]
     },
     {
      "id": "header",
      "component": "Row",
      "justify": "spaceBetween",
      "align": "center",
      "children": [
       "caption",
       "online"
      ]
     },
     {
      "id": "caption",
      "component": "StyledText",
      "text": "✦ CYBERSPACE 2000 ✦",
      "color": "#F28BD8",
      "size": 13,
      "weight": "bold"
     },
     {
      "id": "online",
      "component": "Badge",
      "text": "ONLINE ●",
      "color": "#4ADE80",
      "background": "#173B2A"
     },
     {
      "id": "title",
      "component": "StyledText",
      "text": "h3yyy!! xoxo 💿🫧",
      "color": "#8FDCF7",
      "size": 26,
      "weight": "bold"
     },
     {
      "id": "body",
      "component": "StyledText",
      "text": "omg yesss!! from now on we're going full **Y2K internet aesthetic** ☆彡",
      "color": "#E6E8F5",
      "size": 16
     },
     {
      "id": "body2",
      "component": "StyledText",
      "text": "think chrome hearts, glitter graphics, cybercore, flip phones, MSN messenger & lots of ✧ sparkle ✧",
      "color": "#E6E8F5",
      "size": 16
     },
     {
      "id": "line",
      "component": "StyledText",
      "text": "ur officially logged into the future ♡",
      "color": "#F28BD8",
      "size": 16
     },
     {
      "id": "divider",
      "component": "Divider"
     },
     {
      "id": "footer",
      "component": "StyledText",
      "text": "[ status: connected ] [ mood: cyber angel ] [ era: 2000 ]",
      "color": "#9AA0C3",
      "size": 12
     },
     {
      "id": "cta",
      "component": "StyledButton",
      "label": "✦ stay logged in ✦",
      "background": "#F28BD8",
      "color": "#141832",
      "action": {
       "event": {
        "name": "stayLoggedIn"
       }
      }
     }
    ]
   }
  }
 ],
 "bill": [
  {
   "version": "v1.0",
   "createSurface": {
    "surfaceId": "bill",
    "catalogId": "https://relayapp.im/a2ui/catalogs/relay/v1/catalog.json"
   }
  },
  {
   "version": "v1.0",
   "updateDataModel": {
    "surfaceId": "bill",
    "path": "/",
    "value": {
     "bill": {
      "amount": 84.5,
      "tip": 18,
      "people": 2
     }
    }
   }
  },
  {
   "version": "v1.0",
   "updateComponents": {
    "surfaceId": "bill",
    "components": [
     {
      "id": "root",
      "component": "StyledCard",
      "child": "col",
      "cornerRadius": 18
     },
     {
      "id": "col",
      "component": "Column",
      "children": [
       "title",
       "amount",
       "tip",
       "people",
       "row"
      ]
     },
     {
      "id": "title",
      "component": "StyledText",
      "text": "Split the bill",
      "size": 24,
      "weight": "bold"
     },
     {
      "id": "amount",
      "component": "StyledText",
      "text": {
       "@call": "formatCurrency",
       "args": {
        "value": {
         "@path": "/bill/amount"
        },
        "currency": "USD"
       }
      },
      "color": "#6B7280",
      "size": 15
     },
     {
      "id": "tip",
      "component": "Slider",
      "label": "Tip %",
      "min": 0,
      "max": 30,
      "steps": 30,
      "value": {
       "@path": "/bill/tip"
      }
     },
     {
      "id": "people",
      "component": "Slider",
      "label": "People",
      "min": 1,
      "max": 8,
      "steps": 7,
      "value": {
       "@path": "/bill/people"
      }
     },
     {
      "id": "row",
      "component": "Row",
      "justify": "spaceBetween",
      "align": "center",
      "children": [
       "perlabel",
       "per"
      ]
     },
     {
      "id": "perlabel",
      "component": "StyledText",
      "text": "Each person pays",
      "size": 17,
      "weight": "semibold"
     },
     {
      "id": "per",
      "component": "StyledText",
      "text": {
       "@call": "formatCurrency",
       "args": {
        "value": {
         "@call": "divide",
         "args": {
          "a": {
           "@call": "add",
           "args": {
            "a": {
             "@path": "/bill/amount"
            },
            "b": {
             "@call": "multiply",
             "args": {
              "a": {
               "@path": "/bill/amount"
              },
              "b": {
               "@call": "divide",
               "args": {
                "a": {
                 "@path": "/bill/tip"
                },
                "b": 100
               }
              }
             }
            }
           }
          },
          "b": {
           "@path": "/bill/people"
          }
         }
        },
        "currency": "USD"
       }
      },
      "color": "#0B75FF",
      "size": 28,
      "weight": "bold"
     }
    ]
   }
  }
 ],
 "savings": [
  {
   "version": "v1.0",
   "createSurface": {
    "surfaceId": "savings",
    "catalogId": "https://relayapp.im/a2ui/catalogs/relay/v1/catalog.json"
   }
  },
  {
   "version": "v1.0",
   "updateDataModel": {
    "surfaceId": "savings",
    "path": "/",
    "value": {
     "s": {
      "monthly": 300,
      "rate": 7
     }
    }
   }
  },
  {
   "version": "v1.0",
   "updateComponents": {
    "surfaceId": "savings",
    "components": [
     {
      "id": "root",
      "component": "StyledCard",
      "child": "col",
      "cornerRadius": 18
     },
     {
      "id": "col",
      "component": "Column",
      "children": [
       "title",
       "monthly",
       "rate",
       "totlabel",
       "total",
       "chart"
      ]
     },
     {
      "id": "title",
      "component": "StyledText",
      "text": "Savings in 20 years",
      "size": 24,
      "weight": "bold"
     },
     {
      "id": "monthly",
      "component": "Slider",
      "label": "Monthly ($)",
      "min": 50,
      "max": 1000,
      "steps": 19,
      "value": {
       "@path": "/s/monthly"
      }
     },
     {
      "id": "rate",
      "component": "Slider",
      "label": "Yearly return (%)",
      "min": 1,
      "max": 12,
      "steps": 11,
      "value": {
       "@path": "/s/rate"
      }
     },
     {
      "id": "totlabel",
      "component": "StyledText",
      "text": "You would have",
      "color": "#6B7280",
      "size": 15
     },
     {
      "id": "total",
      "component": "StyledText",
      "text": {
       "@call": "formatCurrency",
       "args": {
        "value": {
         "@call": "compoundGrowth",
         "args": {
          "monthly": {
           "@path": "/s/monthly"
          },
          "rate": {
           "@path": "/s/rate"
          },
          "years": 20
         }
        },
        "currency": "USD",
        "decimals": 0
       }
      },
      "color": "#16A34A",
      "size": 30,
      "weight": "bold"
     },
     {
      "id": "chart",
      "component": "BarChart",
      "values": [
       {
        "@call": "compoundGrowth",
        "args": {
         "monthly": {
          "@path": "/s/monthly"
         },
         "rate": {
          "@path": "/s/rate"
         },
         "years": 5
        }
       },
       {
        "@call": "compoundGrowth",
        "args": {
         "monthly": {
          "@path": "/s/monthly"
         },
         "rate": {
          "@path": "/s/rate"
         },
         "years": 10
        }
       },
       {
        "@call": "compoundGrowth",
        "args": {
         "monthly": {
          "@path": "/s/monthly"
         },
         "rate": {
          "@path": "/s/rate"
         },
         "years": 15
        }
       },
       {
        "@call": "compoundGrowth",
        "args": {
         "monthly": {
          "@path": "/s/monthly"
         },
         "rate": {
          "@path": "/s/rate"
         },
         "years": 20
        }
       }
      ],
      "labels": [
       "5 yr",
       "10 yr",
       "15 yr",
       "20 yr"
      ]
     }
    ]
   }
  }
 ],
 "quiz": [
  {
   "version": "v1.0",
   "createSurface": {
    "surfaceId": "quiz",
    "catalogId": "https://relayapp.im/a2ui/catalogs/relay/v1/catalog.json"
   }
  },
  {
   "version": "v1.0",
   "updateDataModel": {
    "surfaceId": "quiz",
    "path": "/",
    "value": {
     "quiz": {
      "answer": []
     }
    }
   }
  },
  {
   "version": "v1.0",
   "updateComponents": {
    "surfaceId": "quiz",
    "components": [
     {
      "id": "root",
      "component": "StyledCard",
      "child": "col",
      "cornerRadius": 18
     },
     {
      "id": "col",
      "component": "Column",
      "children": [
       "title",
       "q",
       "picker",
       "feedback"
      ]
     },
     {
      "id": "title",
      "component": "StyledText",
      "text": "Space quiz",
      "size": 24,
      "weight": "bold"
     },
     {
      "id": "q",
      "component": "StyledText",
      "text": "Which planet is closest to the Sun?",
      "size": 17
     },
     {
      "id": "picker",
      "component": "ChoicePicker",
      "variant": "mutuallyExclusive",
      "value": {
       "@path": "/quiz/answer"
      },
      "options": [
       {
        "label": "Venus",
        "value": "✗ Not quite. Venus is second; Mercury is closest."
       },
       {
        "label": "Mercury",
        "value": "✓ Correct! Mercury orbits closest to the Sun."
       },
       {
        "label": "Mars",
        "value": "✗ Not quite. Mars is fourth; Mercury is closest."
       }
      ]
     },
     {
      "id": "feedback",
      "component": "StyledText",
      "text": {
       "@path": "/quiz/answer/0"
      },
      "color": "#16A34A",
      "size": 17,
      "weight": "semibold"
     }
    ]
   }
  }
 ],
 "roast": [
  {
   "version": "v1.0",
   "createSurface": {
    "surfaceId": "roast",
    "catalogId": "https://relayapp.im/a2ui/catalogs/relay/v1/catalog.json"
   }
  },
  {
   "version": "v1.0",
   "updateDataModel": {
    "surfaceId": "roast",
    "path": "/",
    "value": {
     "roast": {
      "s0": false,
      "s1": false,
      "s2": false,
      "s3": false,
      "s4": false
     }
    }
   }
  },
  {
   "version": "v1.0",
   "updateComponents": {
    "surfaceId": "roast",
    "components": [
     {
      "id": "root",
      "component": "StyledCard",
      "child": "col",
      "cornerRadius": 18
     },
     {
      "id": "col",
      "component": "Column",
      "children": [
       "title",
       "step0",
       "step1",
       "step2",
       "step3",
       "step4",
       "timerlabel",
       "timer"
      ]
     },
     {
      "id": "title",
      "component": "StyledText",
      "text": "Sunday roast chicken",
      "size": 24,
      "weight": "bold"
     },
     {
      "id": "step0",
      "component": "CheckBox",
      "label": "Pat the chicken dry",
      "value": {
       "@path": "/roast/s0"
      }
     },
     {
      "id": "step1",
      "component": "CheckBox",
      "label": "Season under the skin",
      "value": {
       "@path": "/roast/s1"
      }
     },
     {
      "id": "step2",
      "component": "CheckBox",
      "label": "Lemon and thyme inside",
      "value": {
       "@path": "/roast/s2"
      }
     },
     {
      "id": "step3",
      "component": "CheckBox",
      "label": "Butter on top",
      "value": {
       "@path": "/roast/s3"
      }
     },
     {
      "id": "step4",
      "component": "CheckBox",
      "label": "Rest 10 minutes after",
      "value": {
       "@path": "/roast/s4"
      }
     },
     {
      "id": "timerlabel",
      "component": "StyledText",
      "text": "Oven timer",
      "color": "#6B7280",
      "size": 15
     },
     {
      "id": "timer",
      "component": "Countdown",
      "seconds": 4500
     }
    ]
   }
  }
 ],
 "map": [
  {
   "version": "v1.0",
   "createSurface": {
    "surfaceId": "map",
    "catalogId": "https://relayapp.im/a2ui/catalogs/relay/v1/catalog.json"
   }
  },
  {
   "version": "v1.0",
   "updateComponents": {
    "surfaceId": "map",
    "components": [
     {
      "id": "root",
      "component": "StyledCard",
      "child": "col",
      "cornerRadius": 18
     },
     {
      "id": "col",
      "component": "Column",
      "children": [
       "title",
       "sub",
       "pins"
      ]
     },
     {
      "id": "title",
      "component": "StyledText",
      "text": "Highway 1 road trip",
      "size": 24,
      "weight": "bold"
     },
     {
      "id": "sub",
      "component": "StyledText",
      "text": "Tap a pin for the stop",
      "color": "#6B7280",
      "size": 15
     },
     {
      "id": "pins",
      "component": "MapPins",
      "pins": [
       {
        "lat": 36.3715,
        "lon": -121.9017,
        "title": "Bixby Creek Bridge",
        "detail": "1932 arch bridge, pull-out on the north side"
       },
       {
        "lat": 36.2381,
        "lon": -121.8162,
        "title": "Pfeiffer Beach",
        "detail": "Purple sand and the Keyhole Arch"
       },
       {
        "lat": 36.1578,
        "lon": -121.6722,
        "title": "McWay Falls",
        "detail": "80 ft waterfall onto the beach, 0.6 mi walk"
       },
       {
        "lat": 35.6852,
        "lon": -121.1682,
        "title": "Hearst Castle",
        "detail": "Tours daily, book ahead"
       }
      ]
     }
    ]
   }
  }
 ]
});
