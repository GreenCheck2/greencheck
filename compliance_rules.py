from datetime import datetime, timedelta

def base_rules(product):
    issues = []

    # Universal rules
    if product['thc'] > 35:
        issues.append("❌ THC content exceeds 35% legal limit.")

    package_date = datetime.strptime(product['packaged_date'], '%Y-%m-%d')
    if datetime.now() - package_date > timedelta(days=90):
        issues.append("❌ Product is older than 90 days (sale window violation).")
    if datetime.now() - package_date > timedelta(days=365):
        issues.append("❌ Product exceeds 1-year expiration limit.")

    if not product['batch_id'] or len(product['batch_id']) < 6 or not product['batch_id'].isalnum():
        issues.append("❌ Batch ID is missing or invalid.")

    if product['thc_per_serving'] > 100:
        issues.append("❌ THC per serving exceeds 100mg legal limit.")

    if product['cbd'] is None or product['cbn'] is None:
        issues.append("❌ Missing CBD or CBN values.")

    if product['weight_grams'] <= 0:
        issues.append("❌ Net weight is missing or invalid.")

    if not product.get('warning_label'):
        issues.append("❌ Product is missing a legal warning label.")

    return issues

def check_california(product):
    issues = []
    if product['product_type'] == "edible" and product['thc_per_serving'] > 10:
        issues.append("❌ CA: Edibles must not exceed 10mg THC per serving.")
    return issues

def check_colorado(product):
    issues = []
    if product['product_type'] == "flower" and product['thc'] > 30:
        issues.append("❌ CO: Flower THC % must not exceed 30%.")
    return issues

def check_oklahoma(product):
    issues = []
    if product['product_type'] == "edible" and product['thc_per_serving'] > 50:
        issues.append("❌ OK: Edibles must not exceed 50mg THC per serving.")
    return issues

def check_michigan(product):
    issues = []
    if product['product_type'] == "edible" and product['thc_per_serving'] > 10:
        issues.append("❌ MI: Edibles must not exceed 10mg THC per serving.")
    return issues

def check_new_york(product):
    issues = []
    if product['product_type'] == "vape" and product['thc'] > 70:
        issues.append("❌ NY: Vape products must not exceed 70% THC.")
    return issues

def check_illinois(product):
    issues = []
    if product['product_type'] == "edible" and product['thc_per_serving'] > 10:
        issues.append("❌ IL: Edibles must not exceed 10mg THC per serving.")
    return issues

def check_nevada(product):
    issues = []
    if product['product_type'] == "edible" and product['thc_per_serving'] > 10:
        issues.append("❌ NV: Edibles must not exceed 10mg THC per serving.")
    return issues

def check_massachusetts(product):
    issues = []
    if product['product_type'] == "edible" and product['thc_per_serving'] > 5:
        issues.append("❌ MA: Edibles must not exceed 5mg THC per serving.")
    return issues

def check_louisiana(product):
    issues = []
    if product['product_type'] == "edible" and product['thc_per_serving'] > 50:
        issues.append("❌ LA: Edibles must not exceed 50mg THC per serving.")
    if product['product_type'] == "flower" and product['thc'] > 35:
        issues.append("❌ LA: Flower THC % must not exceed 35%.")
    return issues

def check_topicals(product):
    issues = []
    if product['product_type'] == "topical" and product['thc'] > 0.3:
        issues.append("❌ Topicals must remain non-psychoactive (≤0.3% THC).")
    return issues

def check_state_specific(product):
    state = product.get('state', '').upper()
    if state == 'CA':
        return check_california(product)
    elif state == 'CO':
        return check_colorado(product)
    elif state == 'OK':
        return check_oklahoma(product)
    elif state == 'MI':
        return check_michigan(product)
    elif state == 'NY':
        return check_new_york(product)
    elif state == 'IL':
        return check_illinois(product)
    elif state == 'NV':
        return check_nevada(product)
    elif state == 'MA':
        return check_massachusetts(product)
    elif state == 'LA':
    	return check_louisiana(product)
    return []

def check_compliance(product):
    issues = base_rules(product)
    issues += check_state_specific(product)
    issues += check_topicals(product)
    return issues or ["✅ Product is compliant."]