import random
from thefuzz import fuzz
from database import get_all_banks

def find_similar_by_name(query_name, limit=5):
    """Calcula scores par a par comparando a query com o nome dos bancos salvos."""
    banks = get_all_banks()
    if not banks:
        return []

    results = []
    for bank in banks:
        # Extrai os nomes tratando nulos
        n1 = str(bank['name'] or "").lower()
        n2 = str(bank['fullName'] or "").lower()
        q = query_name.lower()
        
        # Token sort ratio ignora ordem das palavras (ex: "Banco Brasil" vs "Brasil Banco")
        score = max(fuzz.token_sort_ratio(q, n1), fuzz.token_sort_ratio(q, n2))
        
        results.append({
            "bank": bank,
            "score": score
        })
    
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]

def find_similar_by_code(query_code):
    """Busca o código de forma exata ou calcula similaridade de strings para typos."""
    banks = get_all_banks()
    if not banks:
        return None, []

    # Busca Exata
    for bank in banks:
        if bank['code'] is not None and str(bank['code']) == str(query_code):
            return bank, []

    # Tolerância por aproximação (ex: 3410 digitado no lugar de 341)
    results = []
    for bank in banks:
        if bank['code'] is not None:
            score = fuzz.ratio(str(query_code), str(bank['code']))
            results.append({"bank": bank, "score": score})
            
    results.sort(key=lambda x: x["score"], reverse=True)
    return None, results[:5]

def group_by_similarity(threshold=85):
    """Agrupa bancos que possuem nomes com alta similaridade textual."""
    banks = get_all_banks()
    groups = {}
    visited = set()

    for i, bank in enumerate(banks):
        name1 = bank['name'] or bank['fullName'] or ""
        if not name1 or name1 in visited:
            continue
            
        current_group = [bank]
        visited.add(name1)
        
        for j in range(i + 1, len(banks)):
            name2 = banks[j]['name'] or banks[j]['fullName'] or ""
            if not name2 or name2 in visited:
                continue
                
            if fuzz.token_sort_ratio(name1.lower(), name2.lower()) >= threshold:
                current_group.append(banks[j])
                visited.add(name2)
                
        if len(current_group) > 1:
            groups[name1] = current_group
            
    return groups

def correct_name(typed_name):
    """Compara a string digitada e retorna o banco com maior nível de confiança."""
    banks = get_all_banks()
    if not banks:
        return None, 0
        
    best_bank = None
    best_score = -1
    
    for bank in banks:
        name = bank['name'] or bank['fullName'] or ""
        # WRatio manipula strings de tamanhos muito diferentes de forma inteligente
        score = fuzz.WRatio(typed_name.lower(), name.lower())
        if score > best_score:
            best_score = score
            best_bank = bank
            
    return best_bank, best_score

# --- Módulos das Tarefas Bônus ---

def process_batch_correction(list_of_names):
    """BÔNUS: Autocorreção simulada em lote."""
    report = []
    for typed in list_of_names:
        bank, score = correct_name(typed)
        report.append({
            "original": typed,
            "suggested": bank['fullName'] if bank else "Não encontrado",
            "confidence": score
        })
    return report

def generate_quiz_question():
    """BÔNUS: Seleciona um banco e distorce caracteres para criar o quiz."""
    banks = [b for b in get_all_banks() if b['name']]
    if not banks:
        return None, None
    
    chosen = random.choice(banks)
    original = chosen['name']
    
    # Substitui pedaços aleatórios por caracteres especiais
    chars = list(original)
    for _ in range(max(1, len(chars) // 4)):
        idx = random.randint(0, len(chars) - 1)
        if chars[idx].isalpha():
            chars[idx] = random.choice(['@', '#', '*', 'X', '?'])
            
    return "".join(chars), original

def export_synonyms_dictionary(filepath="sinonimos_bancos.txt", threshold=90):
    """BÔNUS: Exporta pares idênticos/sinônimos textuais para arquivo de texto."""
    banks = get_all_banks()
    count = 0
    
    with open(filepath, "w", encoding="utf-8") as f:
        for i in range(len(banks)):
            for j in range(i + 1, len(banks)):
                n1 = banks[i]['name'] or banks[i]['fullName'] or ""
                n2 = banks[j]['name'] or banks[j]['fullName'] or ""
                if n1 and n2 and n1 != n2:
                    score = fuzz.token_sort_ratio(n1.lower(), n2.lower())
                    if score >= threshold:
                        f.write(f"[{n1}] mapeia para => [{n2}] (Confiança: {score}%)\n")
                        count += 1
    return count