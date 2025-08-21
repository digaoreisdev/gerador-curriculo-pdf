import tkinter as tk
from tkinter import font as tkfont, messagebox, filedialog
import json
from fpdf import FPDF

# --- JANELA POP-UP DE EDIÇÃO GENÉRICA ---
class EditorPopup(tk.Toplevel):
    def __init__(self, parent, item_data=None, title="Editar Item"):
        super().__init__(parent)
        self.transient(parent)
        self.title(title)
        self.result = None
        
        self.item_data = item_data if item_data else {}
        self.entries = {}

        # Define os campos com base no título da janela
        if "Experiência" in title:
            fields = ["Cargo", "Empresa", "Período", "Descrição"]
        elif "Formação" in title:
            fields = ["Curso", "Instituição", "Período"]
        else: # Competência
            fields = ["Competência"]

        for i, field in enumerate(fields):
            tk.Label(self, text=f"{field}:").grid(row=i, column=0, sticky='w', padx=10, pady=5)
            entry = tk.Entry(self, width=50)
            entry.grid(row=i, column=1, padx=10, pady=5)
            # CORREÇÃO: Usa .get() para evitar erro se a chave não existir
            entry.insert(0, self.item_data.get(field.lower().replace('ç', 'c').replace('ê', 'e'), ''))
            self.entries[field.lower().replace('ç', 'c').replace('ê', 'e')] = entry

        btn_frame = tk.Frame(self)
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=10)
        tk.Button(btn_frame, text="Salvar", command=self.on_ok).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side='left', padx=5)

        self.grab_set()
        self.wait_window(self)

    def on_ok(self):
        self.result = {key: entry.get() for key, entry in self.entries.items()}
        self.destroy()

# --- FUNÇÕES DE DADOS ---
def carregar_dados():
    try:
        with open('dados_curriculo.json', 'r', encoding='utf-8') as f:
            dados = json.load(f)
            # --- FIX DE DADOS: Garante que competências seja uma lista de dicionários ---
            if 'competencias' in dados and dados['competencias'] and isinstance(dados['competencias'][0], str):
                dados['competencias'] = [{'competencia': c} for c in dados['competencias']]
            return dados
    except (FileNotFoundError, json.JSONDecodeError):
        return {"nome_completo": "", "cargo_desejado": "", "contato": {}, "resumo_profissional": "", "experiencias": [], "formacao": [], "competencias": []}

def salvar_dados():
    # Atualiza os campos de texto simples antes de salvar
    dados_cv['nome_completo'] = entry_nome.get()
    dados_cv['cargo_desejado'] = entry_cargo.get()
    dados_cv['contato']['email'] = entry_email.get()
    dados_cv['contato']['telefone'] = entry_telefone.get()
    dados_cv['resumo_profissional'] = text_resumo.get("1.0", tk.END).strip()
    
    with open('dados_curriculo.json', 'w', encoding='utf-8') as f:
        json.dump(dados_cv, f, indent=2, ensure_ascii=False)
    messagebox.showinfo("Sucesso", "Alterações salvas com sucesso!")

# --- FUNÇÕES CRUD DA UI ---
def refresh_list_ui(frame, data_list, title):
    for widget in frame.winfo_children():
        widget.destroy()
    
    for i, item in enumerate(data_list):
        item_frame = tk.Frame(frame) # Removido relevo para um visual mais limpo
        item_frame.pack(fill='x', padx=5, pady=2)
        item_frame.columnconfigure(0, weight=1) # FIX DE LAYOUT
        
        if "Experiência" in title: text = f"{item.get('cargo','')} - {item.get('empresa','')}"
        elif "Formação" in title: text = f"{item.get('curso','')} - {item.get('instituicao','')}"
        else: text = item.get('competencia', '')
        
        tk.Label(item_frame, text=text, anchor='w').grid(row=0, column=0, sticky='ew')
        btn_edit = tk.Button(item_frame, text="Editar", command=lambda idx=i: edit_item(data_list, idx, frame, title))
        btn_edit.grid(row=0, column=1, padx=2)
        btn_remove = tk.Button(item_frame, text="Remover", command=lambda idx=i: remove_item(data_list, idx, frame, title))
        btn_remove.grid(row=0, column=2, padx=2)

def add_item(data_list, frame, title):
    popup = EditorPopup(janela, title=f"Adicionar {title}")
    if popup.result:
        data_list.append(popup.result)
        refresh_list_ui(frame, data_list, title)

def edit_item(data_list, index, frame, title):
    popup = EditorPopup(janela, item_data=data_list[index], title=f"Editar {title}")
    if popup.result:
        data_list[index] = popup.result
        refresh_list_ui(frame, data_list, title)

def remove_item(data_list, index, frame, title):
    if messagebox.askyesno("Confirmar", "Tem certeza que deseja remover este item?"):
        del data_list[index]
        refresh_list_ui(frame, data_list, title)

# --- FUNÇÃO GERAR PDF (COM FIX) ---
def gerar_pdf():
    try:
        dados = carregar_dados()
        caminho_salvar = filedialog.asksaveasfilename(
            initialfile=f"Curriculo_{dados.get('nome_completo','').replace(' ', '_')}.pdf",
            defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")]
        )
        if not caminho_salvar: return

        pdf = FPDF()
        pdf.add_page(); pdf.set_auto_page_break(auto=True, margin=15)

        # Cabeçalho
        pdf.set_font("Helvetica", "B", 20); pdf.cell(0, 10, dados.get('nome_completo',''), ln=True, align='C')
        # ... (código do cabeçalho sem alterações)
        pdf.set_font("Helvetica", "", 12); pdf.cell(0, 8, dados.get('cargo_desejado',''), ln=True, align='C')
        pdf.set_font("Helvetica", "", 10); contato_str = f"{dados.get('contato',{}).get('email','')} | {dados.get('contato',{}).get('telefone','')} | {dados.get('contato',{}).get('localizacao','')}"
        pdf.cell(0, 6, contato_str, ln=True, align='C'); pdf.line(10, pdf.get_y() + 5, 200, pdf.get_y() + 5); pdf.ln(10)

        def criar_titulo(titulo):
            pdf.set_font("Helvetica", "B", 14); pdf.cell(0, 10, titulo, ln=True, align='L'); pdf.ln(2)

        # Seções
        if dados.get('resumo_profissional'): criar_titulo("Resumo Profissional"); pdf.set_font("Helvetica", "", 11); pdf.multi_cell(0, 6, dados['resumo_profissional']); pdf.ln(5)
        # ... (código de Experiências e Formação sem alterações)
        if dados.get('experiencias'): criar_titulo("Experiências Profissionais"); pdf.set_font("Helvetica", "", 11)
        for exp in dados['experiencias']:
            pdf.set_font(style="B"); pdf.cell(0, 6, f"{exp.get('cargo','')} na {exp.get('empresa','')}", ln=True)
            pdf.set_font(style=""); pdf.cell(0, 6, exp.get('periodo',''), ln=True); pdf.multi_cell(0, 6, exp.get('descricao','')); pdf.ln(4)
        if dados.get('formacao'): criar_titulo("Formação Acadêmica")
        for form in dados['formacao']:
            pdf.set_font(style="B"); pdf.cell(0, 6, f"{form.get('curso','')} - {form.get('instituicao','')}", ln=True)
            pdf.set_font(style=""); pdf.cell(0, 6, form.get('periodo',''), ln=True); pdf.ln(4)

        # FIX DO PDF: Verifica se competências existe e trata os dados corretamente
        if dados.get('competencias'):
            criar_titulo("Competências")
            pdf.set_font("Helvetica", "", 11)
            # Garante que a lista seja de strings para o join
            competencias_list = [c.get('competencia', '') for c in dados['competencias']]
            pdf.multi_cell(0, 6, ", ".join(competencias_list)); pdf.ln(5)

        pdf.output(caminho_salvar)
        messagebox.showinfo("Sucesso", f"PDF gerado com sucesso!\nSalvo em: {caminho_salvar}")
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro ao gerar o PDF:\n{e}")

# --- INTERFACE GRÁFICA PRINCIPAL ---
dados_cv = carregar_dados()
janela = tk.Tk()
janela.title("Editor de Currículo Profissional v3.1")
janela.geometry("850x700")
janela.columnconfigure(0, weight=1); janela.rowconfigure(1, weight=1)

# --- WIDGETS ---
frame_botoes = tk.Frame(janela)
frame_botoes.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
frame_botoes.columnconfigure(1, weight=1)
btn_salvar = tk.Button(frame_botoes, text="Salvar Alterações no JSON", command=salvar_dados, font=("Helvetica", 10, "bold"))
btn_salvar.grid(row=0, column=0, sticky="w")
btn_gerar_pdf = tk.Button(frame_botoes, text="Gerar PDF", command=gerar_pdf, font=("Helvetica", 10, "bold"), bg="#4CAF50", fg="white")
btn_gerar_pdf.grid(row=0, column=2, sticky="e")

main_frame = tk.Frame(janela); main_frame.grid(row=1, column=0, sticky="nsew")
main_frame.rowconfigure(0, weight=1); main_frame.columnconfigure(0, weight=1)
canvas = tk.Canvas(main_frame); canvas.grid(row=0, column=0, sticky="nsew")
scrollbar = tk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview); scrollbar.grid(row=0, column=1, sticky="ns")
canvas.configure(yscrollcommand=scrollbar.set); canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
scrollable_frame = tk.Frame(canvas); canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
# FIX DE LAYOUT: Faz o frame rolável expandir horizontalmente com a janela
scrollable_frame.columnconfigure(0, weight=1)

# --- SEÇÕES DENTRO DO FRAME ROLÁVEL ---
def create_section(parent, text):
    frame = tk.LabelFrame(parent, text=text, padx=10, pady=10)
    frame.pack(fill="x", padx=10, pady=5)
    frame.columnconfigure(1, weight=1) # FIX DE LAYOUT
    return frame

frame_pessoal = create_section(scrollable_frame, "Dados Pessoais")
tk.Label(frame_pessoal, text="Nome:").grid(row=0, column=0, sticky="w"); entry_nome = tk.Entry(frame_pessoal); entry_nome.grid(row=0, column=1, sticky="ew")
# ... (restante dos campos de dados pessoais)
tk.Label(frame_pessoal, text="Cargo:").grid(row=1, column=0, sticky="w"); entry_cargo = tk.Entry(frame_pessoal); entry_cargo.grid(row=1, column=1, sticky="ew")
tk.Label(frame_pessoal, text="Email:").grid(row=2, column=0, sticky="w"); entry_email = tk.Entry(frame_pessoal); entry_email.grid(row=2, column=1, sticky="ew")
tk.Label(frame_pessoal, text="Telefone:").grid(row=3, column=0, sticky="w"); entry_telefone = tk.Entry(frame_pessoal); entry_telefone.grid(row=3, column=1, sticky="ew")
entry_nome.insert(0, dados_cv.get('nome_completo','')); entry_cargo.insert(0, dados_cv.get('cargo_desejado',''))
entry_email.insert(0, dados_cv.get('contato',{}).get('email','')); entry_telefone.insert(0, dados_cv.get('contato',{}).get('telefone',''))

frame_resumo = create_section(scrollable_frame, "Resumo Profissional")
text_resumo = tk.Text(frame_resumo, height=6, wrap=tk.WORD); text_resumo.pack(fill="x", expand=True)
text_resumo.insert('1.0', dados_cv.get('resumo_profissional',''))

# Listas Editáveis
exp_frame = create_section(scrollable_frame, "Experiências Profissionais")
tk.Button(exp_frame, text="+ Adicionar", command=lambda: add_item(dados_cv['experiencias'], exp_list_frame, "Experiência")).pack(anchor='w')
exp_list_frame = tk.Frame(exp_frame); exp_list_frame.pack(fill='x')

form_frame = create_section(scrollable_frame, "Formação Acadêmica")
tk.Button(form_frame, text="+ Adicionar", command=lambda: add_item(dados_cv['formacao'], form_list_frame, "Formação")).pack(anchor='w')
form_list_frame = tk.Frame(form_frame); form_list_frame.pack(fill='x')

comp_frame = create_section(scrollable_frame, "Competências")
tk.Button(comp_frame, text="+ Adicionar", command=lambda: add_item(dados_cv['competencias'], comp_list_frame, "Competência")).pack(anchor='w')
comp_list_frame = tk.Frame(comp_frame); comp_list_frame.pack(fill='x')

# Preenche as listas na inicialização
refresh_list_ui(exp_list_frame, dados_cv.get('experiencias', []), "Experiência")
refresh_list_ui(form_list_frame, dados_cv.get('formacao', []), "Formação")
refresh_list_ui(comp_list_frame, dados_cv.get('competencias', []), "Competência")

janela.mainloop()