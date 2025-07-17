# captioning �� ���� ���� DB ����
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import pandas as pd
import time
import sqlite3

# �� �ε�
model_id = "beomi/KoAlpaca-Polyglot-12.8B"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id, device_map="auto", torch_dtype="auto")
pipe = pipeline("text-generation", model=model, tokenizer=tokenizer)

# ���� ����Ʈ ����
ingredient_list = [
    "���̾ƽžƸ��̵�",
    "�츮�ǻ�",
    "���˷�л�",
    "���ڶ�ƽþ�Ƽī",
    "��Ƽ��"
]

# ĸ�� ���� �Լ�
def generate_description(ingredient):
    prompt = f"""
����� �Ǻ� ���� �м� �������Դϴ�.
���� ���п� ���� �������ּ���: {ingredient}

- ȿ��:
- ���ۿ�:
- ���ǻ���:
- ������ �Ǻ� Ÿ��:
- ���� ��:
- �Բ� ����ϸ� �� �Ǵ� ����:
- ���Ե� ��ǥ ��ǰ:
- ��� �ñ�/����:
"""
    output = pipe(prompt, max_new_tokens=300, do_sample=True, top_k=50, top_p=0.95)[0]['generated_text']
    return output.replace(prompt.strip(), "").strip()

# ��� ����
results = []
for ingredient in ingredient_list:
    print(f"Generating info for: {ingredient}")
    description = generate_description(ingredient)
    results.append({
        "���и�": ingredient,
        "����": description
    })
    time.sleep(1)  # �� ���� ������ ����

# ���������������� ����
df = pd.DataFrame(results)
df.to_csv("ȿ��DB_���м���.csv", index=False, encoding="utf-8-sig")
print("ȿ�� DB ���� �Ϸ�: ȿ��DB_���м���.csv")

# CSV �ε�
df = pd.read_csv("ȿ��DB_���м���.csv")

# SQLite ���� �� ����
conn = sqlite3.connect("skincare_ingredient.db")
df.to_sql("ingredient_descriptions", conn, if_exists="replace", index=False)

print("SQLite DB�� ���� �Ϸ�")
conn.close()
