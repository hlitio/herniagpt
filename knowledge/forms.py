from django import forms

from .models import KnowledgeTopic


class KnowledgeTopicForm(forms.ModelForm):
    class Meta:
        model = KnowledgeTopic
        fields = ["category", "title", "summary", "content", "status"]
        widgets = {
            "category": forms.Select(attrs={
                "class": "w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-sm text-white focus:border-cyan-400/40 focus:outline-none focus:ring-4 focus:ring-cyan-500/10"
            }),
            "title": forms.TextInput(attrs={
                "class": "w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-sm text-white placeholder:text-slate-500 focus:border-cyan-400/40 focus:outline-none focus:ring-4 focus:ring-cyan-500/10",
                "placeholder": "Ej: Conexión a la VPN corporativa con Cisco AnyConnect",
            }),
            "summary": forms.Textarea(attrs={
                "class": "w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-sm text-white placeholder:text-slate-500 focus:border-cyan-400/40 focus:outline-none focus:ring-4 focus:ring-cyan-500/10",
                "rows": 4,
                "placeholder": "Resumen breve del topic",
            }),
            "content": forms.Textarea(attrs={
                "class": "w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-sm text-white placeholder:text-slate-500 focus:border-cyan-400/40 focus:outline-none focus:ring-4 focus:ring-cyan-500/10",
                "rows": 12,
                "placeholder": "Desarrollá aquí el contenido completo del topic",
            }),
            "status": forms.Select(attrs={
                "class": "w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-sm text-white focus:border-cyan-400/40 focus:outline-none focus:ring-4 focus:ring-cyan-500/10"
            }),
        }