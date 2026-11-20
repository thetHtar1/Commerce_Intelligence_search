# လက်ရှိ Dataset ကို NLU အတွက် စစ်ဆေးချက်

## ရည်ရွယ်ချက်နှင့် ကန့်သတ်ချက်

ဒီစစ်ဆေးမှုက `data/training/expression_understanding/` ရှိ လက်ရှိ dataset ကိုသာ အကဲဖြတ်ထားပါတယ်။ Dataset အသစ်၊ query အသစ်၊ label အသစ် မထည့်ထားပါ။ ရည်ရွယ်ချက်က လက်ရှိ schema နဲ့ coverage ဟာ query တစ်ခုလုံးရဲ့ အဓိပ္ပာယ်ကို Structured Search Intent အဖြစ်သင်ယူဖို့ လုံလောက်/မလုံလောက် ဆုံးဖြတ်ပြီး နောက်တစ်ဆင့်လိုအပ်ချက်တွေကို သတ်မှတ်ဖို့ပါ။

## အကျဉ်းချုပ်

လက်ရှိ dataset ဟာ **span-level expression extraction အတွက် seed data** အဖြစ် အသုံးဝင်ပါတယ်။ Hard constraint, soft preference, product attribute, negation, comparison, ambiguity တို့ကို label ပေးထားပြီး query အများစုမှာ annotation အများအပြား ပါဝင်ပါတယ်။

သို့သော် **query တစ်ခုလုံးမှ canonical structured intent ကို တိုက်ရိုက်သင်ယူဖို့ မပြည့်စုံသေးပါ**။ Query-level target JSON မရှိပါ၊ `intent_summary` 98 ခုလုံး အလွတ်ဖြစ်ပါတယ်၊ negation scope နဲ့ cross-entity relation မသိမ်းထားပါ၊ ဥပမာအားလုံးက constructed English query တွေဖြစ်ပြီး human review မပြီးသေးပါ။ ဒါကြောင့် လက်ရှိ split ပေါ်က model score ကို production NLU အရည်အသွေးအဖြစ် မယူသင့်ပါ။

## Dataset လက်ရှိအခြေအနေ

| အတိုင်းအတာ | လက်ရှိအခြေအနေ |
|---|---:|
| Lexicon entries | 164 |
| Queries | 98 |
| Span annotations | 175 |
| Unique query များ | 98 |
| Domain အရေအတွက် | 9 |
| Constructed query များ | 98 / 98 |
| `requires_human_review` ဖြစ်နေသော query များ | 98 / 98 |
| အလွတ် `intent_summary` များ | 98 / 98 |

Query တစ်ခုစီမှာ annotation 1 ခုရှိတာ 24 ခု၊ 2 ခုရှိတာ 71 ခု၊ 3 ခုရှိတာ 3 ခု ဖြစ်ပါတယ်။ Annotation label စုစုပေါင်းမှာ `hard_constraint` 57, `soft_preference` 37, `product_attribute` 41, `negation` 11, `comparison` 5, `ambiguous_expression` 24 ခု ပါဝင်ပါတယ်။

Domain ဖြန့်ဝေမှုမှာ electronics 39 ခု၊ furniture 20 ခု၊ beauty 11 ခု၊ fashion 9 ခု၊ home 7 ခု၊ appliances 6 ခု၊ general 4 ခု၊ food 1 ခု၊ local_search 1 ခု ဖြစ်ပါတယ်။ Query အားလုံး English ဖြစ်ပြီး language column မရှိပါ။

## Schema စစ်ဆေးချက်

လက်ရှိ query row တွင် `query_id`, `query`, `domain`, `expression_annotations`, `intent_summary`, `data_origin`, `annotation_status` ပါဝင်ပါတယ်။ Annotation row တွင် `text`, `label`, `attribute`, `operator`, `value`, `unit`, `contextual_role`, `confidence` ပါဝင်ပါတယ်။

### ကောင်းမွန်နေသောအချက်များ

- Annotation တစ်ခုစီကို query context ထဲက contiguous text span နဲ့ချိတ်ထားပါတယ်။
- Label တွေက hard/soft, product attribute, negation, comparison, ambiguity ကို ခွဲနိုင်ပါတယ်။
- Numeric constraints တွင် operator, value, unit ထည့်ရန် validation ရှိပါတယ်။
- Negation annotation တွင် excluded target ကို `value` အဖြစ် မှတ်တမ်းတင်ထားပါတယ်။
- CSV/JSONL ကိုက်ညီမှု၊ duplicate ID/query၊ invalid label၊ overlapping span စစ်ဆေးမှုရှိပါတယ်။

### Query-level NLU အတွက် မလုံလောက်သေးသောအချက်များ

- `intent_summary` သည် row 98 ခုလုံး အလွတ်ဖြစ်ပြီး `expected_intent` ကဲ့သို့ validated JSON target မရှိပါ။ လက်ရှိ target က span တစ်ခုချင်း label ဖြစ်ပြီး product, attributes, constraints, preferences တွေကို query အဆင့်မှာ ပေါင်းစပ်ထားတဲ့ output မဟုတ်ပါ။
- `domain` က coarse category သာဖြစ်ပြီး `product_category`, `query_type`, `language` ကို label မလုပ်ထားပါ။
- Span ကို `text` နဲ့ပဲ မှတ်ထားပြီး character `start` / `end` offset မရှိပါ။ Phrase ထပ်ပေါ်တဲ့ query တွေမှာ ဘယ် occurrence ကိုဆိုလိုတယ်ဆိုတာ မတိကျနိုင်ပါ။
- Annotation တွေကြားမှာ `and`, `but`, `or`, clause, target, scope တို့ရဲ့ relation ကို မသိမ်းထားပါ။ `contextual_role` ဟာ short text ဖြစ်ပြီး controlled value သို့မဟုတ် cross-span link မဟုတ်ပါ။
- Annotation operator တွင် `<`, `<=`, `>`, `>=` ကိုသုံးပြီး downstream intent ဥပမာများတွင် `lt`, `lte`, `gt`, `gte` လိုအပ်ပါတယ်။ Mapping က label guide မှာရှိပေမယ့် schema-level canonical enum မဟုတ်သေးပါ။
- `product_attribute` label တစ်ခုတည်းနဲ့ hard requirement လား soft preference လား မဆုံးဖြတ်နိုင်ပါ။ Context စာသားက အဲဒီကွာခြားချက်ကို ဖော်ပြနိုင်ပေမယ့် explicit `modality`/`force` field မရှိပါ။

## ရည်မှန်းထားတဲ့ NLU coverage နဲ့ လက်ရှိ coverage

| Coverage အမျိုးအစား | လက်ရှိ coverage | အကဲဖြတ်ချက် |
|---|---|---|
| Sentence-level meaning | Query တစ်ခုလုံး ရှိသော်လည်း 98 ခုလုံးမှာ query-level intent target မရှိ | Gap — query-to-JSON supervised output ကို မသင်နိုင်သေး |
| Context-dependent expressions | `lightweight` ကို Q012/Q013/Q049 တွင် context အလိုက် label မတူစွာ သုံးထားသည်; phrase 17 ခု ပြန်တွေ့သည် | အစရှိသော်လည်း systematic contrast sets မရှိ |
| Negation scope | Negation span 11 ခု, query 11 ခု; `won't dry out my hair` မပါ | Gap — scope, affected attribute, effect negation, clause attachment ကို သီးခြားမသိမ်းထား |
| Multiple constraints | Annotation 2+ ခုပါတဲ့ query 74 ခု; hard constraint 2+ ခုပါတဲ့ query 6 ခု | အလယ်အလတ် — constraint အရေအတွက်ရှိပေမယ့် relation/precedence မရှိ |
| Paraphrase variation | Operator နဲ့ wording အမျိုးမျိုးရှိသော်လည်း paraphrase group ID မရှိ၊ complete annotation signature ပြန်တူသော query မရှိ | Gap — intent တူသော paraphrase များကို တစ်စုတည်းသင်/တိုင်းတာမရ |
| Ambiguity | `ambiguous_expression` span 24 ခုကို query 20 ခုတွင် တွေ့ရသည် | အစရှိသော်လည်း query-level clarification need/choice ကို label မလုပ်ထား |
| Comparison | Comparison span 5 ခုကို query 3 ခုတွင် တွေ့ရသည် | အားနည်း — reference entity, desired direction, multiple comparison target မလုံလောက် |
| Unseen-expression generalization | 92 template group; split ကြား template leakage 0 | Template leakage ကို ကာကွယ်ထားသော်လည်း unseen-expression စမ်းသပ်မှု မဟုတ်သေး |
| Label quality | Query အားလုံး `requires_human_review` | Gold training/evaluation data မဖြစ်သေး |

### Negation နှင့် scope မှတ်ချက်

လက်ရှိ negation ဥပမာအများစုက `without fragrance`, `excluding Lenovo`, `not leather`, `not refurbished`, `except black` လို သတ်မှတ်ချက်တစ်ခုကို ဖယ်ထုတ်တဲ့ပုံစံဖြစ်ပါတယ်။ ဥပမာ user ပေးထားတဲ့ “that won't dry out my hair” က product ထဲက ingredient ကို မပါစေချင်တာနဲ့ မတူဘဲ product effect ကို ရှောင်လိုတဲ့ အဓိပ္ပာယ်ဖြစ်ပါတယ်။ လက်ရှိ label schema မှာ ဒီကွာခြားချက်၊ negation ရဲ့ scope, target attribute နဲ့ clause link ကို သီးခြားဖော်ပြနိုင်ခြင်း မရှိပါ။

### Paraphrase နှင့် split မှတ်ချက်

“under”, “below”, “not more than”, “at most” စတဲ့ price wording မျိုးစုံ ရှိပါတယ်။ ဒါပေမယ့် query အားလုံးမှာ `paraphrase_group_id` မရှိသလို expected intent တူကြောင်း သတ်မှတ်ထားတဲ့ pair မရှိပါ။ လက်ရှိ 92-template grouped split မှာ template မတူအောင် ထားနိုင်ပေမယ့် annotation expression-label တူညီမှုက train/validation ကြား 6 ခု၊ train/test ကြား 4 ခု ထပ်နေပါတယ်။ ထို့ကြောင့် split သည် template generalization ကိုသာ အနည်းငယ်စမ်းသပ်ပြီး unseen expression ကို မစမ်းသပ်ပါ။

## Validation အခြေအနေ

`python src/query_understanding/validate_dataset.py` ကို run လုပ်ရာ structural validation **PASS (0 errors)** ဖြစ်ပါတယ်။ Warning 2 ခုက query 98 ခုလုံး human review လိုနေခြင်းနဲ့ `intent_summary` 98 ခုလုံး အလွတ်ဖြစ်ခြင်းဖြစ်ပါတယ်။ လက်ရှိ split မှာ train 67, validation 16, test 15 ဖြစ်ပြီး delexicalized template leakage 0 ဖြစ်ပါတယ်။ ဒီ structural pass က annotation အဓိပ္ပာယ်မှန်ကန်တယ်လို့ အတည်မပြုပါ။

## နောက်တစ်ဆင့် ဆုံးဖြတ်ရန်

1. လက်ရှိ span annotation များကို ဆက်ထိန်းထားပြီး query-level `expected_intent` JSON ကို canonical schema အဖြစ် သတ်မှတ်ရန်။ Intent အတွင်းရှိ attribute, constraint, preference တစ်ခုစီကို မူရင်း query ရှိ source span offset နှင့် ချိတ်ရန်။
2. Span အတွက် character `start`/`end`, `polarity`, `modality` (hard/soft/descriptive), `scope`, `target_id` နှင့် normalized operator/value/unit ကို သတ်မှတ်ရန်.
3. Negation, multiple constraint, context, paraphrase အတွက် `contrast_set_id`, `paraphrase_group_id`, `template_id` metadata ကို annotation workflow ထဲတွင် ထည့်ရန် — လက်ရှိအဆင့်မှာ data row အသစ် မထည့်ဘဲ schema ဆုံးဖြတ်ချက်အဖြစ်သာထားရန်.
4. Human review/adjudication ပြီးမှ canonical intent ကို gold label အဖြစ် အသုံးပြုရန်.
5. Evaluation တွင် template-held-out အပြင် expression-held-out နဲ့ contrast/paraphrase-held-out split များကို သီးခြားအစီရင်ခံရန်; query-level intent exact match, slot F1, negation/scope accuracy, clarification accuracy ကို တိုင်းတာရန်.

## Files စစ်ဆေးထားသည်

- `data/training/expression_understanding/contextual_query_examples.csv`
- `data/training/expression_understanding/contextual_query_examples.jsonl`
- `data/training/expression_understanding/expression_lexicon.csv`
- `docs/label_guide.md`
- `src/query_understanding/validate_dataset.py`
- `src/query_understanding/split_dataset.py`
- `data/processed/expression_understanding/v1/split_summary.json`
