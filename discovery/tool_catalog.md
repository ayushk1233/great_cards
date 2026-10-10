# Tool catalog (verbatim from tools/list)

Server: `https://bk-api.bankkaro.com/mcp` — captured 2026-10-10T18:32:45.303356+00:00

14 tools.


## `whatsapp_get_next_question`

- Required: `[]`
- outputSchema: no · annotations: None

### Description

```text
WhatsApp facade: Given partial user state, return exactly one next question to ask. Use this to keep chat flows short and deterministic.
```

### Input schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "user_goal": {
      "default": "unknown",
      "type": "string",
      "enum": [
        "recommendation",
        "category_recommendation",
        "compare",
        "card_details",
        "eligibility",
        "unknown"
      ]
    },
    "category": {
      "type": "string",
      "enum": [
        "fuel",
        "shopping",
        "dining",
        "grocery",
        "food_delivery",
        "travel",
        "utility"
      ]
    },
    "known_spends": {
      "default": {},
      "type": "object",
      "properties": {
        "amazon_spends": {
          "type": "number",
          "minimum": 0
        },
        "flipkart_spends": {
          "type": "number",
          "minimum": 0
        },
        "other_online_spends": {
          "type": "number",
          "minimum": 0
        },
        "other_offline_spends": {
          "type": "number",
          "minimum": 0
        },
        "grocery_spends_online": {
          "type": "number",
          "minimum": 0
        },
        "offline_grocery": {
          "type": "number",
          "minimum": 0
        },
        "online_food_ordering": {
          "type": "number",
          "minimum": 0
        },
        "fuel": {
          "type": "number",
          "minimum": 0
        },
        "dining_or_going_out": {
          "type": "number",
          "minimum": 0
        },
        "flights_annual": {
          "type": "number",
          "minimum": 0
        },
        "hotels_annual": {
          "type": "number",
          "minimum": 0
        },
        "domestic_lounge_usage_quarterly": {
          "type": "number",
          "minimum": 0
        },
        "international_lounge_usage_quarterly": {
          "type": "number",
          "minimum": 0
        },
        "mobile_phone_bills": {
          "type": "number",
          "minimum": 0
        },
        "electricity_bills": {
          "type": "number",
          "minimum": 0
        },
        "water_bills": {
          "type": "number",
          "minimum": 0
        },
        "insurance_health_annual": {
          "type": "number",
          "minimum": 0
        },
        "insurance_car_or_bike_annual": {
          "type": "number",
          "minimum": 0
        },
        "rent": {
          "type": "number",
          "minimum": 0
        },
        "school_fees": {
          "type": "number",
          "minimum": 0
        },
        "life_insurance": {
          "type": "number",
          "minimum": 0
        }
      }
    },
    "has_income": {
      "default": false,
      "type": "boolean"
    },
    "has_pincode": {
      "default": false,
      "type": "boolean"
    },
    "has_employment_status": {
      "default": false,
      "type": "boolean"
    },
    "card_aliases": {
      "default": [],
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  }
}
```


## `whatsapp_recommend_cards_for_spend_profile`

- Required: `['spend_profile']`
- outputSchema: no · annotations: None

### Description

```text
WhatsApp facade: Recommend top cards from a structured spend profile. Returns compact cards, annual value, fees, links, and a short WhatsApp-ready summary.
```

### Input schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "spend_profile": {
      "type": "object",
      "properties": {
        "amazon_spends": {
          "type": "number",
          "minimum": 0
        },
        "flipkart_spends": {
          "type": "number",
          "minimum": 0
        },
        "other_online_spends": {
          "type": "number",
          "minimum": 0
        },
        "other_offline_spends": {
          "type": "number",
          "minimum": 0
        },
        "grocery_spends_online": {
          "type": "number",
          "minimum": 0
        },
        "offline_grocery": {
          "type": "number",
          "minimum": 0
        },
        "online_food_ordering": {
          "type": "number",
          "minimum": 0
        },
        "fuel": {
          "type": "number",
          "minimum": 0
        },
        "dining_or_going_out": {
          "type": "number",
          "minimum": 0
        },
        "flights_annual": {
          "type": "number",
          "minimum": 0
        },
        "hotels_annual": {
          "type": "number",
          "minimum": 0
        },
        "domestic_lounge_usage_quarterly": {
          "type": "number",
          "minimum": 0
        },
        "international_lounge_usage_quarterly": {
          "type": "number",
          "minimum": 0
        },
        "mobile_phone_bills": {
          "type": "number",
          "minimum": 0
        },
        "electricity_bills": {
          "type": "number",
          "minimum": 0
        },
        "water_bills": {
          "type": "number",
          "minimum": 0
        },
        "insurance_health_annual": {
          "type": "number",
          "minimum": 0
        },
        "insurance_car_or_bike_annual": {
          "type": "number",
          "minimum": 0
        },
        "rent": {
          "type": "number",
          "minimum": 0
        },
        "school_fees": {
          "type": "number",
          "minimum": 0
        },
        "life_insurance": {
          "type": "number",
          "minimum": 0
        }
      },
      "description": "Structured user spend profile. Monthly fields are monthly INR; annual fields end in _annual."
    },
    "top_n": {
      "default": 3,
      "type": "integer",
      "minimum": 1,
      "maximum": 5
    }
  },
  "required": [
    "spend_profile"
  ]
}
```


## `whatsapp_recommend_cards_for_category_spend`

- Required: `['category', 'amount']`
- outputSchema: no · annotations: None

### Description

```text
WhatsApp facade: Recommend cards for one category and amount, e.g. fuel 10000. Returns compact WhatsApp-ready recommendations.
```

### Input schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "category": {
      "type": "string",
      "enum": [
        "fuel",
        "shopping",
        "dining",
        "grocery",
        "food_delivery",
        "travel",
        "utility"
      ]
    },
    "amount": {
      "type": "number",
      "exclusiveMinimum": 0,
      "description": "Spend amount in INR. Defaults to monthly unless amount_period is annual. Travel defaults to annual."
    },
    "amount_period": {
      "type": "string",
      "enum": [
        "monthly",
        "annual"
      ]
    },
    "top_n": {
      "default": 3,
      "type": "integer",
      "minimum": 1,
      "maximum": 5
    }
  },
  "required": [
    "category",
    "amount"
  ]
}
```


## `whatsapp_compare_cards`

- Required: `['card_aliases']`
- outputSchema: no · annotations: None

### Description

```text
WhatsApp facade: Compare 2-3 card aliases with optional spend profile. Returns a deterministic compact comparison and optional winner.
```

### Input schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "card_aliases": {
      "minItems": 2,
      "maxItems": 3,
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "spend_profile": {
      "type": "object",
      "properties": {
        "amazon_spends": {
          "type": "number",
          "minimum": 0
        },
        "flipkart_spends": {
          "type": "number",
          "minimum": 0
        },
        "other_online_spends": {
          "type": "number",
          "minimum": 0
        },
        "other_offline_spends": {
          "type": "number",
          "minimum": 0
        },
        "grocery_spends_online": {
          "type": "number",
          "minimum": 0
        },
        "offline_grocery": {
          "type": "number",
          "minimum": 0
        },
        "online_food_ordering": {
          "type": "number",
          "minimum": 0
        },
        "fuel": {
          "type": "number",
          "minimum": 0
        },
        "dining_or_going_out": {
          "type": "number",
          "minimum": 0
        },
        "flights_annual": {
          "type": "number",
          "minimum": 0
        },
        "hotels_annual": {
          "type": "number",
          "minimum": 0
        },
        "domestic_lounge_usage_quarterly": {
          "type": "number",
          "minimum": 0
        },
        "international_lounge_usage_quarterly": {
          "type": "number",
          "minimum": 0
        },
        "mobile_phone_bills": {
          "type": "number",
          "minimum": 0
        },
        "electricity_bills": {
          "type": "number",
          "minimum": 0
        },
        "water_bills": {
          "type": "number",
          "minimum": 0
        },
        "insurance_health_annual": {
          "type": "number",
          "minimum": 0
        },
        "insurance_car_or_bike_annual": {
          "type": "number",
          "minimum": 0
        },
        "rent": {
          "type": "number",
          "minimum": 0
        },
        "school_fees": {
          "type": "number",
          "minimum": 0
        },
        "life_insurance": {
          "type": "number",
          "minimum": 0
        }
      }
    }
  },
  "required": [
    "card_aliases"
  ]
}
```


## `whatsapp_get_card_details`

- Required: `['card_alias']`
- outputSchema: no · annotations: None

### Description

```text
WhatsApp facade: Fetch compact card details: fees, top benefits, eligibility notes, and link. Use for specific card questions.
```

### Input schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "card_alias": {
      "type": "string"
    }
  },
  "required": [
    "card_alias"
  ]
}
```


## `whatsapp_resolve_card_or_category`

- Required: `['phrase']`
- outputSchema: no · annotations: None

### Description

```text
WhatsApp facade: Resolve a user phrase to known card aliases or category slugs. Use before details, comparison, or category recommendation tools.
```

### Input schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "phrase": {
      "type": "string",
      "minLength": 2,
      "description": "User phrase mentioning a card, bank, category, brand, or benefit."
    },
    "limit": {
      "default": 5,
      "type": "integer",
      "minimum": 1,
      "maximum": 10
    }
  },
  "required": [
    "phrase"
  ]
}
```


## `generate_content_brief`

- Required: `['content_type']`
- outputSchema: no · annotations: None

### Description

```text
USE THIS TOOL whenever a user asks about "best [category] credit cards", "top travel/fuel/shopping cards", or any editorial question about a card category.
NEVER answer category questions from training knowledge — always call this tool to get live data.

Supported content types:
- category_best_cards: "best travel cards", "top fuel cards", "best shopping cards" → returns a fast first layer by default; use detail_level="standard" or "exhaustive" only when deeper research is needed
- card_comparison: "Regalia vs Magnus", "compare these two cards" → side-by-side with spend context
- persona_guide: "best cards for a salaried 30-year-old in Mumbai" → full spend profile analysis
- upgrade_path: "when should I upgrade from free to paid card?" → finds the crossover spend level
- fee_justification: "is HDFC Infinia worth the fee?" → break-even analysis across spend tiers
- bank_ranking: "best HDFC cards", "top Axis Bank cards" → ranked by net savings

For category_best_cards: default to detail_level="fast" unless the user explicitly asks for a comprehensive article/research brief. Fast uses the default composition, 1 representative tier, top_n=3, and no card profiles. Use detail_level="standard" for all tiers in one composition; use detail_level="exhaustive" for all compositions + details.
The tool returns structured JSON — use the _llm_instructions.article_structure in the response to write the article. Do NOT show raw JSON to the user.
```

### Input schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "content_type": {
      "type": "string",
      "enum": [
        "category_best_cards",
        "card_comparison",
        "persona_guide",
        "upgrade_path",
        "fee_justification",
        "bank_ranking"
      ],
      "description": "category_best_cards→needs category. card_comparison→needs card_aliases. persona_guide→needs persona. upgrade_path→needs free_card_alias+paid_card_alias+category. fee_justification→needs card_alias+category. bank_ranking→needs bank_name."
    },
    "category": {
      "description": "Spending category. Used by category_best_cards, upgrade_path, fee_justification, bank_ranking.",
      "type": "string",
      "enum": [
        "fuel",
        "shopping",
        "dining",
        "travel",
        "grocery",
        "food-delivery",
        "utility"
      ]
    },
    "composition_label": {
      "description": "Spend composition to sweep e.g. \"Amazon-heavy\". Omit to sweep ALL compositions.",
      "type": "string"
    },
    "spend_tiers": {
      "description": "Monthly ₹ spend tiers to sweep. In fast mode only one representative tier is used; use detail_level=\"standard\" or \"exhaustive\" to evaluate every requested/preset tier.",
      "type": "array",
      "items": {
        "type": "number"
      }
    },
    "detail_level": {
      "default": "fast",
      "description": "Controls latency and payload size. fast=default composition + 1 representative tier + no card profiles. standard=default composition + all category tiers + no card profiles. exhaustive=all compositions + all tiers + card profiles. Use exhaustive only when the user explicitly asks for deep research.",
      "type": "string",
      "enum": [
        "fast",
        "standard",
        "exhaustive"
      ]
    },
    "per_call_timeout_ms": {
      "description": "Timeout for each backend calculation/detail request. Defaults: 6000ms fast, 8000ms standard, 10000ms exhaustive. Timed-out jobs return partial results instead of failing the whole tool.",
      "type": "number"
    },
    "card_aliases": {
      "description": "2-4 card aliases for card_comparison. Get from list_cards.",
      "minItems": 2,
      "maxItems": 4,
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "spend_profile": {
      "description": "Spend map {category:₹/month} for card_comparison or persona_guide.",
      "type": "object",
      "propertyNames": {
        "type": "string"
      },
      "additionalProperties": {
        "type": "number"
      }
    },
    "persona": {
      "description": "Persona for persona_guide: name, spends map, optional income+priorities.",
      "type": "object",
      "properties": {
        "name": {
          "type": "string"
        },
        "monthly_income": {
          "type": "number"
        },
        "spends": {
          "type": "object",
          "propertyNames": {
            "type": "string"
          },
          "additionalProperties": {
            "type": "number"
          }
        },
        "priorities": {
          "type": "array",
          "items": {
            "type": "string"
          }
        }
      },
      "required": [
        "name",
        "spends"
      ]
    },
    "free_card_alias": {
      "description": "Free/entry card alias for upgrade_path.",
      "type": "string"
    },
    "paid_card_alias": {
      "description": "Premium card alias for upgrade_path.",
      "type": "string"
    },
    "card_alias": {
      "description": "Card alias for fee_justification.",
      "type": "string"
    },
    "bank_name": {
      "description": "Bank name for bank_ranking e.g. \"HDFC Bank\".",
      "type": "string"
    },
    "top_n": {
      "description": "Number of top cards per spend tier. Defaults: 3 for fast, 5 for standard/exhaustive. fast caps this at 3 to keep responses small.",
      "type": "number"
    },
    "include_details": {
      "description": "Fetch detailed card profiles. Defaults false for fast/standard and true for exhaustive. Set true only when the next answer needs card-level fee/benefit deep dives.",
      "type": "boolean"
    },
    "output_format": {
      "description": "Output format. carousel=Instagram JSON, reels=voiceover script, thread=X thread, linkedin=LinkedIn post, blog=article.",
      "type": "string",
      "enum": [
        "blog",
        "carousel",
        "reels",
        "thread",
        "linkedin"
      ]
    },
    "audience": {
      "description": "Target audience persona.",
      "type": "string",
      "enum": [
        "first-timer",
        "rewards-seeker",
        "traveler",
        "young-pro",
        "high-spender",
        "budget"
      ]
    },
    "goal": {
      "description": "awareness=inform, consideration=evaluate, conversion=push to apply.",
      "type": "string",
      "enum": [
        "awareness",
        "consideration",
        "conversion"
      ]
    },
    "hook": {
      "description": "Narrative angle. savings-math=₹ calc lead, worth-fee=ROI, hidden-gems=underrated benefits.",
      "type": "string",
      "enum": [
        "benefits-led",
        "savings-math",
        "mistakes",
        "hidden-gems",
        "worth-fee",
        "upgrade-story"
      ]
    },
    "spend_focus": {
      "description": "Spend category to spotlight in examples.",
      "type": "string",
      "enum": [
        "online-shopper",
        "flyer",
        "foodie",
        "fuel-heavy",
        "bills",
        "all-round"
      ]
    },
    "tone": {
      "description": "Writing tone.",
      "type": "string",
      "enum": [
        "conversational",
        "punchy",
        "educational",
        "story-driven",
        "expert"
      ]
    },
    "language": {
      "description": "hinglish=mix English+Hindi for Indian millennials.",
      "type": "string",
      "enum": [
        "english",
        "hinglish"
      ]
    },
    "comparison_card": {
      "description": "Card alias to compare against inline.",
      "type": "string"
    },
    "seo_keyword": {
      "description": "SEO keyword for blog H1 and subheadings.",
      "type": "string"
    }
  },
  "required": [
    "content_type"
  ]
}
```


## `run_api_diagnostics`

- Required: `[]`
- outputSchema: no · annotations: None

### Description

```text
Run backend/API smoke tests for Great.Cards without exposing secrets.
Use this for API QA, deployment validation, schema drift checks, flaky-tool debugging, or "is the MCP/API healthy?" questions.
Default scope="quick" checks listing, one card details call, and recommendation calculate. Use scope="full" for category listing + eligibility too.
Returns per-check latency, pass/fail/timeout status, sanitized samples when requested, and a next debug step.
```

### Input schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "scope": {
      "default": "quick",
      "description": "quick runs core API checks with small payloads. full adds category listing and eligibility checks.",
      "type": "string",
      "enum": [
        "quick",
        "full"
      ]
    },
    "timeout_ms": {
      "default": 8000,
      "description": "Per-check timeout in milliseconds. Defaults to 8000.",
      "type": "number"
    },
    "include_samples": {
      "default": false,
      "description": "Include small sanitized response samples for debugging schema drift. Samples never include credentials.",
      "type": "boolean"
    }
  }
}
```


## `recommend_cards`

- Required: `[]`
- outputSchema: no · annotations: None

### Description

```text
PERSONALIZED credit card recommendations based on the user's actual spending pattern.
Analyzes 100+ Indian credit cards and ranks by NET ANNUAL SAVINGS (rewards earned + lounge value + milestone benefits - joining fee - annual fee).

PRE-REQUISITE: If you haven't called get_advisor_context yet this session, call it FIRST to load brand mappings and conversation flow. Without it, you'll mismap brands to spending keys.

WHEN TO USE: User provides specific spending amounts OR mentions brands/categories they spend on.
WHEN NOT TO USE: User just wants to browse cards without spending context -> use list_cards instead.

SPENDING KEY MAPPING (CRITICAL — map user mentions to correct keys):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• amazon_spends → Amazon.in ONLY
• flipkart_spends → Flipkart ONLY
• other_online_spends → ALL other e-commerce: Myntra, Meesho, Nykaa, Ajio, Tata CLiQ, Croma online, BookMyShow, Ola, Uber rides, PharmEasy, NetMeds, 1mg, Lenskart, Pepperfry, Urban Company, CRED bills, subscription boxes
• other_offline_spends → Physical store purchases: malls, retail, electronics stores, local markets, salons, gyms, medical stores, any POS/tap/swipe
• grocery_spends_online → Online grocery ONLY: BigBasket, Blinkit, Zepto, Swiggy Instamart, JioMart, Amazon Fresh, Flipkart Grocery, DMart Ready
• online_food_ordering → Food DELIVERY: Swiggy (food, not Instamart), Zomato, EatSure, Dominos/Pizza Hut online orders
• fuel → Petrol pumps: HP, Indian Oil, BPCL, Shell, Nayara, Reliance
• dining_or_going_out → IN-PERSON restaurants, cafes (Starbucks, CCD, Third Wave), bars, pubs, food courts
• flights_annual → ANNUAL flight spend (all airlines, all booking platforms) — convert monthly×12
• hotels_annual → ANNUAL hotel/stay spend (hotels, Airbnb, OYO) — convert monthly×12
• domestic_lounge_usage_quarterly → Domestic lounge visits PER QUARTER — "fly 4x/year" = 1/quarter
• international_lounge_usage_quarterly → International lounge visits PER QUARTER
• mobile_phone_bills → Jio, Airtel, Vi, BSNL monthly bills
• electricity_bills → Monthly electricity bill
• water_bills → Monthly water bill
• insurance_health_annual → ANNUAL health insurance premium — convert monthly×12
• insurance_car_or_bike_annual → ANNUAL vehicle insurance — convert monthly×12
• rent → Monthly rent (via CRED RentPay, NoBroker, etc.)
• school_fees → Monthly education fees (school, coaching, college)
• offline_grocery → Monthly physical grocery store spend: DMart, Reliance Smart/Fresh, Nature's Basket, 24Seven, kirana stores, liquor stores
• life_insurance → ANNUAL life insurance premium: LIC, HDFC Life, SBI Life, ICICI Prudential, Max Life, Tata AIA, term plans, ULIPs
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

VAGUE QUERY HANDLING:
• "best card for shopping" → ask what they buy and where, OR estimate: amazon_spends=5000, flipkart_spends=3000, other_online_spends=5000
• "premium card" → suggest high spenders profile: flights_annual=100000, hotels_annual=50000, dining=10000, domestic_lounge_usage_quarterly=3
• "I spend a lot on food" → clarify: delivery (online_food_ordering) vs dining out (dining_or_going_out) vs groceries (grocery_spends_online)
• "cashback card" → focus on the user's biggest spending categories for maximum net savings
• "travel card" → ask about flights, hotels, lounges; these drive the biggest travel card differentiation

IMPORTANT UNITS:
• Most fields are MONTHLY amounts in ₹ (including offline_grocery)
• flights_annual, hotels_annual, insurance_health_annual, insurance_car_or_bike_annual, life_insurance are ANNUAL — multiply monthly by 12
• lounge fields are PER QUARTER — divide annual visits by 4
• All fee outputs include 18% GST
```

### Input schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "amazon_spends": {
      "description": "Monthly Amazon spending in ₹ (Amazon ONLY — not other e-commerce)",
      "type": "number"
    },
    "flipkart_spends": {
      "description": "Monthly Flipkart spending in ₹ (Flipkart ONLY — not other e-commerce)",
      "type": "number"
    },
    "other_online_spends": {
      "description": "Monthly OTHER online shopping in ₹. INCLUDES: Myntra, Meesho, Nykaa, Ajio, Tata CLiQ, Croma online, BookMyShow, Ola, Uber cabs, PharmEasy, NetMeds, 1mg, Lenskart, Pepperfry, Urban Company. EXCLUDES: Amazon, Flipkart, Swiggy/Zomato food, BigBasket/Blinkit/Zepto groceries (these have their own keys)",
      "type": "number"
    },
    "other_offline_spends": {
      "description": "Monthly offline/in-store spending in ₹. INCLUDES: malls, retail stores, clothing shops, electronics stores (Croma/Reliance Digital in-store), local markets, salons, gyms, medical/pharmacy in-store, any physical swipe/tap. EXCLUDES: restaurants (use dining_or_going_out), petrol pumps (use fuel), grocery stores if buying online (use grocery_spends_online)",
      "type": "number"
    },
    "grocery_spends_online": {
      "description": "Monthly ONLINE grocery spending in ₹. INCLUDES: BigBasket, Blinkit, Zepto, Swiggy Instamart, JioMart, Amazon Fresh, Flipkart Grocery, DMart Ready, Nature's Basket online. EXCLUDES: physical grocery stores (use offline_grocery), Swiggy/Zomato restaurant food delivery (use online_food_ordering)",
      "type": "number"
    },
    "online_food_ordering": {
      "description": "Monthly food DELIVERY spending in ₹. INCLUDES: Swiggy food delivery, Zomato food delivery, EatSure, Box8, Dominos online, Pizza Hut online. EXCLUDES: dining at restaurants in person (use dining_or_going_out), Swiggy Instamart/grocery (use grocery_spends_online)",
      "type": "number"
    },
    "fuel": {
      "description": "Monthly fuel/petrol/diesel spending in ₹ at petrol pumps. INCLUDES: HP, Indian Oil (IOCL), Bharat Petroleum (BPCL), Shell, Nayara, Reliance petrol pumps. Key: many cards offer fuel surcharge waiver (1% saving on every fill)",
      "type": "number"
    },
    "dining_or_going_out": {
      "description": "Monthly restaurant/dining OUT spending in ₹. INCLUDES: restaurants, cafes (Starbucks, CCD, Third Wave), bars, pubs, cloud kitchens dine-in, food courts. This is IN-PERSON dining only. EXCLUDES: food delivery apps (use online_food_ordering)",
      "type": "number"
    },
    "flights_annual": {
      "description": "ANNUAL flight ticket spending in ₹ (NOT monthly). INCLUDES: domestic and international flights booked on MakeMyTrip, Cleartrip, EaseMyTrip, airline websites (IndiGo, Air India, Vistara, SpiceJet, AirAsia), Google Flights. Convert monthly to annual if user gives monthly",
      "type": "number"
    },
    "hotels_annual": {
      "description": "ANNUAL hotel/stay spending in ₹ (NOT monthly). INCLUDES: hotels, resorts, Airbnb, OYO, MakeMyTrip stays, Booking.com, Goibibo. Convert monthly to annual if user gives monthly",
      "type": "number"
    },
    "domestic_lounge_usage_quarterly": {
      "description": "Domestic airport lounge visits PER QUARTER (not monthly, not annual). If user says \"I fly 4 times a year\" → that's ~1 per quarter. If \"twice a month\" → ~6 per quarter. Common: Priority Pass, DreamFolks, individual bank lounges. Valued at ₹750 per visit",
      "type": "number"
    },
    "international_lounge_usage_quarterly": {
      "description": "International airport lounge visits PER QUARTER. Valued at ₹1,250 per visit. Most relevant for frequent international travelers",
      "type": "number"
    },
    "mobile_phone_bills": {
      "description": "Monthly mobile/phone bill in ₹. INCLUDES: Jio, Airtel, Vi (Vodafone-Idea), BSNL postpaid/prepaid recharges",
      "type": "number"
    },
    "electricity_bills": {
      "description": "Monthly electricity bill in ₹. INCLUDES: state discom bills, Tata Power, Adani Electricity, BSES, CESC",
      "type": "number"
    },
    "water_bills": {
      "description": "Monthly water bill in ₹",
      "type": "number"
    },
    "insurance_health_annual": {
      "description": "ANNUAL health insurance premium in ₹ (NOT monthly). INCLUDES: Star Health, HDFC Ergo, ICICI Lombard, Max Bupa, Niva Bupa, employer top-up plans. Convert monthly to annual if needed",
      "type": "number"
    },
    "insurance_car_or_bike_annual": {
      "description": "ANNUAL vehicle insurance premium in ₹ (NOT monthly). INCLUDES: car and two-wheeler insurance — comprehensive, third-party, own-damage",
      "type": "number"
    },
    "rent": {
      "description": "Monthly rent payment in ₹. INCLUDES: rent paid via CRED RentPay, NoBroker, MagicBricks RentPay, Paytm, or directly on credit card. Note: most rent platforms charge 1-2% convenience fee, so net benefit depends on card reward rate exceeding this",
      "type": "number"
    },
    "school_fees": {
      "description": "Monthly school/education fees in ₹. INCLUDES: school tuition, coaching (Aakash, Allen, FIITJEE, Byju's, Unacademy), college fees, university fees paid on credit card",
      "type": "number"
    },
    "offline_grocery": {
      "description": "Monthly OFFLINE/physical grocery store spending in ₹. INCLUDES: DMart, Reliance Smart, Reliance Fresh, Nature's Basket, 24Seven, local kirana stores, supermarkets, liquor stores — any in-person grocery/household purchase. EXCLUDES: online grocery apps (use grocery_spends_online)",
      "type": "number"
    },
    "life_insurance": {
      "description": "ANNUAL life insurance premium in ₹ (NOT monthly). INCLUDES: LIC, HDFC Life, SBI Life, ICICI Prudential Life, Max Life, Tata AIA Life, Bajaj Allianz Life, PNB MetLife, term plans, endowment plans, ULIPs. EXCLUDES: health insurance (use insurance_health_annual), vehicle insurance (use insurance_car_or_bike_annual)",
      "type": "number"
    },
    "top_n": {
      "default": 5,
      "description": "Number of top cards to return (default 5)",
      "type": "number"
    },
    "response_format": {
      "default": "full",
      "description": "\"full\" = detailed breakdown per card, \"brief\" = card name + net savings + fees only, \"comparison\" = table-friendly flat structure",
      "type": "string",
      "enum": [
        "full",
        "brief",
        "comparison"
      ]
    }
  }
}
```


## `get_card_details`

- Required: `['card_alias']`
- outputSchema: no · annotations: None

### Description

```text
Get FULL details of a specific credit card by its alias/slug.
Returns: fees (with 18% GST), all benefits, rewards structure, eligibility, ratings.
NOTE: If you haven't called get_advisor_context yet, do so first — it has the full card alias reference.

WHEN TO USE: After recommend_cards or list_cards, when the user wants to deep-dive into a specific card.
ALSO USE WHEN: User names a specific card like "tell me about HDFC Regalia" — construct the alias as lowercase-hyphenated bank-card-name (e.g. "hdfc-regalia-gold-credit-card").

COMMON CARD ALIAS PATTERNS (aliases are NOT predictable — use list_cards if unsure):
• HDFC: hdfc-regalia-gold, hdfc-millenia-credit-card, hdfc-swiggy-credit-card, hdfc-infinia-credit-card, hdfc-diners-club-black, hdfc-diners-club-black-metal-credit-card, hdfc-diners-privilege-credit-card, hdfc-freedom-credit-card, hdfc-indian-oil-credit-card, hdfc-pixel-play-credit-card, hdfc-rupay-credit-card, hdfc-indigo-credit-card, HDFC-Moneyback-Credit-Card, hdfc-moneyback-plus-credit-card, hdfc-marriott-bonvoy-credit-card, hdfc-tata-neu-plus-credit-card, hdfc-irctc-credit-card, shoppers-stop-black-hdfc-credit-card, paytm-hdfc-bank-select-credit-card, hdfc-bharat-credit-card, hdfc-superia-airline-credit-card, hdfc-biz-grow-credit-card, hdfc-biz-first-credit-card
• Axis: axis-bank-magnus-credit-card, axis-flipkart-credit-card, axis-privilege-amex-credit-card, axis-atlas-credit-card, axis-neo-credit-card, axis-bank-myzone-credit-card, axis-horizon-credit-card, axis-cashback-credit-card, axis-indian-oil-rupay-credit-card, axis-select-credit-card, axis-airtel-credit-card, axis-aura-credit-card, axis-rewards-credit-card, axis-samsung-infinite-credit-card, axis-bank-privilege-credit-card, axis-shopper-stop-credit-card
• SBI: sbi-cashback-credit-card, sbi-elite-card, sbi-aurum-credit-card, sbi-simply-click-credit-card, sbi-bpcl-octane-credit-card, flipkart-sbi-credit-card, tata-neu-infinity-sbi-credit-card, irctc-sbi-platinum-card, sbi-simply-save-credit-card, sbi-prime-credit-card, sbi-card-pulse-credit-card
• ICICI: icici-amazon-pay-credit-card, icici-sapphiro-credit-card, icici-hpcl-coral-credit-card, icici-rubyx-credit-card, icici-platinum-chip-credit-card, makemytrip-icici-signature, icici-hpcl-super-saver-credit-card, times-black-credit-card
• IDFC: idfc-first-millennia-credit-card, idfc-first-select-credit-card, idfc-first-classic-credit-card, idfc-first-wow-credit-card, idfc-wealth-credit-card, idfc-first-private-credit-card, idfc-swyp-credit-card, idfc-ashva-credit-card, idfc-mayura-credit-card
• Others: scapia-credit-card, au-altura-credit-card, au-altura-plus-credit-card, au-nomo-credit-card, au-zenith-credit-card, zagg-rupay-credit-card, hsbc-travel-one, hsbc-live-plus-credit-card, standard-charted-ultimate, amex-platinum-travel-credit-card, american-express-platinum-card, amex-gold-credit-card, kotak-zen-signature-credit-card, indusind-legend-credit-card, rbl-world-safari-credit-card, yes-bank-ace-credit-card, jupiter-edge-credit-card
⚠️ ALIAS QUIRKS: Some aliases have mixed case (HDFC-Moneyback-Credit-Card), typos (standard-charted-ultimate), or missing suffixes (hdfc-diners-club-black has no -credit-card). ALWAYS use list_cards to verify.

IMPORTANT: Aliases are inconsistent (some have -credit-card suffix, some don't, some use bank name, some don't). ALWAYS use list_cards first if you're not 100% sure of the alias.

PRESENT: lead with card+bank+one-line positioning. Show fee block: "Joining ₹X | Annual ₹Y | Waiver: Z". Top 3-5 benefits relevant to user.
ELIGIBILITY: show as "Age X-Y | ₹X LPA salaried / ₹Y LPA self-emp | CIBIL XXX". Check against user's stated profile proactively.
Never invent rates not in the data. Never add GST again (fees already include 18% GST).
```

### Input schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "card_alias": {
      "type": "string",
      "description": "The SEO alias/slug of the card (e.g. \"hdfc-regalia-gold-credit-card\")"
    }
  },
  "required": [
    "card_alias"
  ]
}
```


## `list_cards`

- Required: `[]`
- outputSchema: no · annotations: None

### Description

```text
Browse and filter credit cards without needing spending data.
NOTE: If you haven't called get_advisor_context yet, do so first — it has category mappings and feature-to-filter rules.

WHEN TO USE: User wants to explore/discover cards, asks about a category, or hasn't shared spending details.
WHEN NOT TO USE: User has given spending amounts -> use recommend_cards for personalized ranking.

CATEGORY MAPPING (map user intent to category slug):
• "premium" / "luxury" / "lounge access" / "travel" / "airport" → best-travel-credit-card
• "shopping" / "cashback" / "online shopping" / "rewards" → best-shopping-credit-card
• "fuel" / "petrol" / "diesel" / "fuel surcharge" → best-fuel-credit-card
• "dining" / "restaurant" / "food" (in-person) / "Starbucks" → best-dining-credit-card
• "grocery" / "BigBasket" / "Blinkit" / "Zepto" → best-cards-grocery-shopping
• "Swiggy" / "Zomato" / "food delivery" → online-food-ordering
• "utility" / "bills" / "recharge" / "electricity" → best-utility-credit-card
• "all cards" / no specific category → leave empty

USER INTENT → FILTER MAPPING:
• "free card" / "no fee" / "LTF" / "lifetime free" / "no annual charge" → free_cards="true"
• "Amex" / "American Express" → card_networks=["American Express"]
• "works internationally" → card_networks=["Visa"] or ["Mastercard"]
• "RuPay" / "UPI linked" → card_networks=["RuPay"]
• "budget card" / "entry level" → annual_fees="0-500" or free_cards="true"
• "super premium" / "invite only" → annual_fees="10000+"
• "HDFC card" / "Axis card" etc → use bank_ids if known, otherwise suggest using recommend_cards

COMMON FOLLOW-UP: After listing, user often picks a card → use get_card_details for the deep dive.
```

### Input schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "category": {
      "default": "",
      "description": "Card category filter. Map user intent: \"premium/luxury/lounge\" → best-travel-credit-card, \"cashback/shopping/online\" → best-shopping-credit-card, \"petrol/diesel\" → best-fuel-credit-card, \"restaurants/cafes/bars\" → best-dining-credit-card, \"BigBasket/Blinkit/Zepto\" → best-cards-grocery-shopping, \"Swiggy/Zomato food delivery\" → online-food-ordering, \"bills/recharge/utilities\" → best-utility-credit-card. Leave empty for all cards.",
      "type": "string",
      "enum": [
        "best-fuel-credit-card",
        "best-shopping-credit-card",
        "best-dining-credit-card",
        "best-travel-credit-card",
        "best-cards-grocery-shopping",
        "online-food-ordering",
        "best-utility-credit-card",
        ""
      ]
    },
    "annual_fees": {
      "default": "",
      "description": "Fee range filter. \"free\" = lifetime free (LTF) cards. Ranges: \"500-1000\", \"1000-2000\", \"2000-5000\", \"5000-10000\", \"10000+\". When user says \"no annual fee\" or \"LTF\" or \"lifetime free\" → use \"free\". When user says \"premium\" they usually mean 5000+ fee range.",
      "type": "string"
    },
    "card_networks": {
      "default": [],
      "description": "Filter by card network: \"Visa\", \"Mastercard\", \"RuPay\", \"American Express\". User hints: \"Amex\" = \"American Express\", \"works at Costco\" = \"Visa\", \"UPI linking\" or \"government cashback\" = \"RuPay\", \"international acceptance\" = \"Visa\" or \"Mastercard\"",
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "bank_ids": {
      "default": [],
      "description": "Filter by bank numeric IDs. Usually not needed unless user names a specific bank.",
      "type": "array",
      "items": {
        "type": "number"
      }
    },
    "credit_score": {
      "default": "",
      "description": "Credit score filter",
      "type": "string"
    },
    "sort_by": {
      "default": "",
      "description": "Sort option (default: priority/popularity)",
      "type": "string"
    },
    "free_cards": {
      "default": "",
      "description": "Set to \"true\" for lifetime free cards only. Use when user says \"free\", \"no fee\", \"LTF\", \"no annual charge\", \"zero fee\"",
      "type": "string"
    },
    "limit": {
      "default": 10,
      "description": "Max cards to return (default 10)",
      "type": "number"
    },
    "response_format": {
      "default": "full",
      "description": "\"full\" = all details, \"brief\" = name + bank + fee only",
      "type": "string",
      "enum": [
        "full",
        "brief"
      ]
    }
  }
}
```


## `compare_cards`

- Required: `['card_aliases']`
- outputSchema: no · annotations: None

### Description

```text
Compare 2-3 credit cards side by side.
NOTE: If you haven't called get_advisor_context yet, do so first — it has correct card alias patterns.

WHEN TO USE: User is deciding between specific cards, says "X vs Y", or asks "which is better".
REQUIRES: card_aliases from previous recommend_cards or list_cards results.

Present the comparison highlighting the differences that matter for the user's use case.
Common comparisons: HDFC Regalia vs Axis Magnus, SBI Cashback vs ICICI Amazon Pay, HDFC Swiggy vs Axis Flipkart.
```

### Input schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "card_aliases": {
      "minItems": 2,
      "maxItems": 3,
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "2-3 card aliases to compare (e.g. [\"hdfc-regalia-gold-credit-card\", \"axis-magnus-credit-card\"])"
    }
  },
  "required": [
    "card_aliases"
  ]
}
```


## `check_eligibility`

- Required: `['pincode', 'annual_income', 'employment_status']`
- outputSchema: no · annotations: None

### Description

```text
Check which cards a user can actually APPLY for based on pincode, income, and employment.
NOTE: If you haven't called get_advisor_context yet, do so first — it has income conversion rules and employment mapping.

WHEN TO USE: User asks "can I get this card?", "which cards am I eligible for?", "I earn X, what can I get?", or before recommending cards to someone with a stated income.

INCOME CONVERSION (users state income in many ways):
• "50k/month" or "50k per month" → annual_income = "600000"
• "10 LPA" or "10 lakhs per annum" → annual_income = "1000000"
• "1.5L/month" → annual_income = "1800000"
• "8 lakhs" (ambiguous) → likely annual, so "800000"

EMPLOYMENT MAPPING:
• Salaried: full-time, part-time, contract workers, government employees
• Self-employed: freelancers, business owners, consultants, doctors/lawyers/CAs with own practice, gig workers, YouTubers, influencers

IDEAL FLOW: check_eligibility first → then recommend_cards with spending to find the BEST eligible card.
```

### Input schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "pincode": {
      "type": "string",
      "minLength": 6,
      "maxLength": 6,
      "description": "6-digit Indian pincode. Common city codes: Delhi 110001, Mumbai 400001, Bangalore 560001, Hyderabad 500001, Chennai 600001, Kolkata 700001, Pune 411001, Ahmedabad 380001, Gurgaon 122001, Noida 201301. Ask the user if not provided."
    },
    "annual_income": {
      "type": "string",
      "description": "Annual in-hand income in ₹ as a string (e.g. \"1200000\" for 12 LPA). Convert from monthly: multiply by 12. Convert from LPA: \"10 LPA\" = \"1000000\". Convert from \"per month\": \"1L/month\" = \"1200000\""
    },
    "employment_status": {
      "type": "string",
      "enum": [
        "salaried",
        "self_employed"
      ],
      "description": "\"salaried\" = full-time employee, part-time, contract. \"self_employed\" = freelancer, business owner, consultant, gig worker, professional (doctor/lawyer/CA with own practice)"
    }
  },
  "required": [
    "pincode",
    "annual_income",
    "employment_status"
  ]
}
```


## `get_advisor_context`

- Required: `[]`
- outputSchema: no · annotations: None

### Description

```text
CALL THIS FIRST before starting any credit card advisory conversation.

Returns the complete CardGenius advisory playbook: conversation flow logic, 700+ brand-to-spending-key mappings, correlated category pairs, unit conversion rules, persona handling, vague query responses, and Indian credit card domain knowledge.

WITHOUT this context, you will:
- Mismap brands to wrong spending keys (e.g. putting Swiggy Instamart under food delivery instead of grocery)
- Miss correlated categories (e.g. asking about flights but forgetting hotels and lounges)
- Get units wrong (e.g. treating annual insurance as monthly)
- Not know how to handle vague queries, personas, or feature requests

USAGE:
- Call with topic="full" at the START of every conversation (~13K tokens, covers everything)
- Or call with a specific topic for targeted context: "brand_mappings", "correlated_pairs", "unit_conversion", "personas", "domain_knowledge", etc.
- You only need to call this ONCE per session — the context applies to all subsequent interactions.

FOR CHATBOT DEVELOPERS: Call this at session init and inject the "context" field into your system prompt.
```

### Input schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "topic": {
      "default": "tool_guide",
      "description": "Which context to load. Use \"full\" for the complete advisory playbook (~13K tokens — recommended on first call). Use specific topics for targeted context: \"brand_mappings\" (700+ brands), \"correlated_pairs\" (related categories to ask together), \"unit_conversion\" (monthly vs annual vs quarterly rules), \"personas\" (student, traveler, business owner templates), \"domain_knowledge\" (fees, rewards, lounges, banks, networks).",
      "type": "string",
      "enum": [
        "full",
        "conversation_flow",
        "data_collection",
        "brand_mappings",
        "correlated_pairs",
        "unit_conversion",
        "feature_mapping",
        "personas",
        "vague_queries",
        "presentation",
        "guardrails",
        "tool_guide",
        "domain_knowledge"
      ]
    }
  }
}
```
