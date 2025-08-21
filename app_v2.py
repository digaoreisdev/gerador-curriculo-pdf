# app_v2.py
import tkinter as tk
from tkinter import font as tkfont, messagebox, filedialog
import json
import os

try:
    from jinja2 import Environment, FileSystemLoader
    from weasyprint import HTML, CSS
    WEASYPRINT_DISPONIVEL = True
except ImportError:
    WEASYPRINT_DISPONIVEL = False

# --- JANELA POP-UP DE EDIÇÃO (Atualizada para Projetos) ---
class EditorPopup(tk.Toplevel):
    def __init__(self, parent, item_data=None, title="Editar Item"):
        super().__init__(parent)
        self.transient(parent)
        self.title(title)
        self.result = None
        self.item_data = item_data if item_data else {}
        self.entries = {}

        field_map = {
            "Experiência": {"Cargo": "cargo", "Empresa": "empresa", "Período": "periodo", "Descrição": "descricao"},
            "Formação": {"Curso": "curso", "Instituição": "instituicao", "Período": "periodo"},
            "Competência": {"Competência": "competencia"},
            "Rede Social": {"Rede": "rede", "URL": "url"},
            "Projeto": {"Nome": "nome", "Link": "link", "Descrição": "descricao"} # Novo campo
        }

        current_fields = None
        for key in field_map:
            if key in title:
                current_fields = field_map[key]
                break
        
        if not current_fields: self.destroy(); return

        for i, (label, json_key) in enumerate(current_fields.items()):
            tk.Label(self, text=f"{label}:").grid(row=i, column=0, sticky='w', padx=10, pady=5)
            
            widget = None
            if label == "Descrição":
                widget = tk.Text(self, width=48, height=5, wrap=tk.WORD)
                widget.grid(row=i, column=1, padx=10, pady=5)
                widget.insert('1.0', self.item_data.get(json_key, ''))
            else:
                widget = tk.Entry(self, width=50)
                widget.grid(row=i, column=1, padx=10, pady=5)
                widget.insert(0, self.item_data.get(json_key, ''))
            
            self.entries[json_key] = widget
            
        btn_frame = tk.Frame(self)
        btn_frame.grid(row=len(current_fields), column=0, columnspan=2, pady=10)
        tk.Button(btn_frame, text="Salvar", command=self.on_ok).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side='left', padx=5)
        self.grab_set(); self.wait_window(self)

    def on_ok(self):
        self.result = {}
        for key, widget in self.entries.items():
            if isinstance(widget, tk.Text): self.result[key] = widget.get("1.0", tk.END).strip()
            else: self.result[key] = widget.get()
        self.destroy()

# --- FUNÇÕES DE DADOS (Atualizada para Projetos) ---
def carregar_dados_json():
    try:
        with open('dados_curriculo.json', 'r', encoding='utf-8') as f:
            dados = json.load(f)
            if 'competencias' in dados and dados.get('competencias') and isinstance(dados['competencias'][0], str):
                dados['competencias'] = [{'competencia': c} for c in dados['competencias']]
            if 'redes_sociais' not in dados: dados['redes_sociais'] = []
            if 'projetos' not in dados: dados['projetos'] = [] # Novo campo
            return dados
    except (FileNotFoundError, json.JSONDecodeError):
        return {"nome_completo": "", "cargo_desejado": "", "contato": {}, "resumo_profissional": "", "experiencias": [], "formacao": [], "competencias": [], "redes_sociais": [], "projetos": []}

def salvar_dados_json():
    dados_cv['nome_completo'] = entry_nome.get()
    dados_cv['cargo_desejado'] = entry_cargo.get()
    dados_cv['contato']['email'] = entry_email.get()
    dados_cv['contato']['telefone'] = entry_telefone.get()
    dados_cv['resumo_profissional'] = text_resumo.get("1.0", tk.END).strip()
    with open('dados_curriculo.json', 'w', encoding='utf-8') as f:
        json.dump(dados_cv, f, indent=2, ensure_ascii=False)
    messagebox.showinfo("Sucesso", "Alterações salvas com sucesso no arquivo JSON!")

def update_scrollregion():
    canvas.update_idletasks()
    canvas.configure(scrollregion=canvas.bbox("all"))

# --- FUNÇÕES CRUD DA UI (Atualizada para Projetos) ---
def refresh_list_ui(frame, data_list, title):
    for widget in frame.winfo_children(): widget.destroy()
    for i, item in enumerate(data_list):
        item_frame = tk.Frame(frame)
        item_frame.pack(fill='x', padx=5, pady=2)
        item_frame.columnconfigure(0, weight=1)
        text = ""
        if "Experiência" in title: text = f"{item.get('cargo','')} - {item.get('empresa','')}"
        elif "Formação" in title: text = f"{item.get('curso','')} - {item.get('instituicao','')}"
        elif "Competência" in title: text = item.get('competencia', '')
        elif "Rede Social" in title: text = f"{item.get('rede','')} - {item.get('url','')}"
        elif "Projeto" in title: text = item.get('nome', '') # Novo campo
        tk.Label(item_frame, text=text, anchor='w').grid(row=0, column=0, sticky='ew')
        btn_edit = tk.Button(item_frame, text="Editar", command=lambda idx=i: edit_item(data_list, idx, frame, title)); btn_edit.grid(row=0, column=1, padx=2)
        btn_remove = tk.Button(item_frame, text="Remover", command=lambda idx=i: remove_item(data_list, idx, frame, title)); btn_remove.grid(row=0, column=2, padx=2)
    update_scrollregion()

def add_item(data_list, frame, title):
    popup = EditorPopup(janela, title=f"Adicionar {title}")
    if popup.result: data_list.append(popup.result); refresh_list_ui(frame, data_list, title)

def edit_item(data_list, index, frame, title):
    popup = EditorPopup(janela, item_data=data_list[index], title=f"Editar {title}")
    if popup.result: data_list[index] = popup.result; refresh_list_ui(frame, data_list, title)

def remove_item(data_list, index, frame, title):
    if messagebox.askyesno("Confirmar", "Tem certeza que deseja remover este item?"):
        del data_list[index]; refresh_list_ui(frame, data_list, title)

def gerar_pdf_final():
    if not WEASYPRINT_DISPONIVEL: messagebox.showerror("Erro de Dependência", "Bibliotecas WeasyPrint ou Jinja2 não encontradas."); return
    salvar_dados_json()
    dados = carregar_dados_json()
    nome_arquivo_saida = filedialog.asksaveasfilename(
        initialfile=f"Curriculo_{dados.get('nome_completo','').replace(' ', '_')}.pdf",
        defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")]
    )
    if not nome_arquivo_saida: return
    try:
        env = Environment(loader=FileSystemLoader('.'))
        template = env.get_template('template.html')
        html_renderizado = template.render(dados=dados)
        stylesheet = CSS('estilo.css')
        HTML(string=html_renderizado).write_pdf(nome_arquivo_saida, stylesheets=[stylesheet])
        messagebox.showinfo("Sucesso", f"PDF gerado com sucesso!\nSalvo em: {nome_arquivo_saida}")
    except Exception as e:
        if isinstance(e, PermissionError): messagebox.showerror("Erro de Permissão", f"Não foi possível salvar o arquivo.\n\nVerifique se o PDF já não está aberto em outro programa.\n\nDetalhes: {e}")
        else: messagebox.showerror("Erro ao Gerar PDF", f"Ocorreu um erro ao gerar o PDF:\n{e}")

# --- INTERFACE GRÁFICA PRINCIPAL (Atualizada para Projetos) ---
dados_cv = carregar_dados_json()
janela = tk.Tk()
janela.title("Gerador de Currículo Visual v9.4 - Final")
janela.geometry("850x700")
janela.columnconfigure(0, weight=1); janela.rowconfigure(1, weight=1)
font_bold = tkfont.Font(family="Helvetica", size=10, weight="bold")
frame_botoes = tk.Frame(janela)
frame_botoes.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
frame_botoes.columnconfigure(1, weight=1)
btn_salvar = tk.Button(frame_botoes, text="Salvar Alterações", command=salvar_dados_json, font=font_bold)
btn_salvar.grid(row=0, column=0, sticky="w")
btn_gerar_pdf = tk.Button(frame_botoes, text="Gerar PDF", command=gerar_pdf_final, font=font_bold, bg="#4CAF50", fg="white")
btn_gerar_pdf.grid(row=0, column=2, sticky="e")
main_frame = tk.Frame(janela); main_frame.grid(row=1, column=0, sticky="nsew")
main_frame.rowconfigure(0, weight=1); main_frame.columnconfigure(0, weight=1)
canvas = tk.Canvas(main_frame); canvas.grid(row=0, column=0, sticky="nsew")
scrollbar = tk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview); scrollbar.grid(row=0, column=1, sticky="ns")
canvas.configure(yscrollcommand=scrollbar.set)
canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
scrollable_frame = tk.Frame(canvas); canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
scrollable_frame.columnconfigure(0, weight=1)

def create_section(parent, text):
    frame = tk.LabelFrame(parent, text=text, padx=10, pady=10)
    frame.pack(fill="x", padx=10, pady=5)
    frame.columnconfigure(1, weight=1)
    return frame

# --- Seções da UI ---
frame_pessoal = create_section(scrollable_frame, "Dados Pessoais")
tk.Label(frame_pessoal, text="Nome:").grid(row=0, column=0, sticky="w"); entry_nome = tk.Entry(frame_pessoal); entry_nome.grid(row=0, column=1, sticky="ew")
tk.Label(frame_pessoal, text="Cargo:").grid(row=1, column=0, sticky="w"); entry_cargo = tk.Entry(frame_pessoal); entry_cargo.grid(row=1, column=1, sticky="ew")
tk.Label(frame_pessoal, text="Email:").grid(row=2, column=0, sticky="w"); entry_email = tk.Entry(frame_pessoal); entry_email.grid(row=2, column=1, sticky="ew")
tk.Label(frame_pessoal, text="Telefone:").grid(row=3, column=0, sticky="w"); entry_telefone = tk.Entry(frame_pessoal); entry_telefone.grid(row=3, column=1, sticky="ew")
entry_nome.insert(0, dados_cv.get('nome_completo','')); entry_cargo.insert(0, dados_cv.get('cargo_desejado',''))
entry_email.insert(0, dados_cv.get('contato',{}).get('email','')); entry_telefone.insert(0, dados_cv.get('contato',{}).get('telefone',''))

social_frame = create_section(scrollable_frame, "Redes Sociais (LinkedIn, GitHub, etc)")
tk.Button(social_frame, text="+ Adicionar", command=lambda: add_item(dados_cv['redes_sociais'], social_list_frame, "Rede Social")).pack(anchor='w')
social_list_frame = tk.Frame(social_frame); social_list_frame.pack(fill='x')

frame_resumo = create_section(scrollable_frame, "Resumo Profissional")
text_resumo = tk.Text(frame_resumo, height=6, wrap=tk.WORD); text_resumo.pack(fill="x", expand=True)
text_resumo.insert('1.0', dados_cv.get('resumo_profissional',''))

# NOVA SEÇÃO: Projetos
proj_frame = create_section(scrollable_frame, "Projetos")
tk.Button(proj_frame, text="+ Adicionar", command=lambda: add_item(dados_cv['projetos'], proj_list_frame, "Projeto")).pack(anchor='w')
proj_list_frame = tk.Frame(proj_frame); proj_list_frame.pack(fill='x')

exp_frame = create_section(scrollable_frame, "Experiências Profissionais")
tk.Button(exp_frame, text="+ Adicionar", command=lambda: add_item(dados_cv['experiencias'], exp_list_frame, "Experiência")).pack(anchor='w')
exp_list_frame = tk.Frame(exp_frame); exp_list_frame.pack(fill='x')

form_frame = create_section(scrollable_frame, "Formação Acadêmica")
tk.Button(form_frame, text="+ Adicionar", command=lambda: add_item(dados_cv['formacao'], form_list_frame, "Formação")).pack(anchor='w')
form_list_frame = tk.Frame(form_frame); form_list_frame.pack(fill='x')

comp_frame = create_section(scrollable_frame, "Competências")
tk.Button(comp_frame, text="+ Adicionar", command=lambda: add_item(dados_cv['competencias'], comp_list_frame, "Competência")).pack(anchor='w')
comp_list_frame = tk.Frame(comp_frame); comp_list_frame.pack(fill='x')

# --- Refresh inicial da UI ---
refresh_list_ui(social_list_frame, dados_cv.get('redes_sociais', []), "Rede Social")
refresh_list_ui(proj_list_frame, dados_cv.get('projetos', []), "Projeto")
refresh_list_ui(exp_list_frame, dados_cv.get('experiencias', []), "Experiência")
refresh_list_ui(form_list_frame, dados_cv.get('formacao', []), "Formação")
refresh_list_ui(comp_list_frame, dados_cv.get('competencias', []), "Competência")
update_scrollregion()
janela.mainloop()