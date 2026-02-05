const { createApp, ref, onMounted, computed } = Vue

createApp({
    setup() {
        // --- ESTADOS ---
        const operadoras = ref([])
        const page = ref(1)
        const limit = ref(10)
        const totalRegistros = ref(0)
        const search = ref('')
        const loading = ref(false)

        // Novos estados para o Modal
        const modalAberto = ref(false)
        const operadoraSelecionada = ref({})
        const historico = ref([])
        const loadingDetalhes = ref(false)

        const totalPaginas = computed(() => Math.ceil(totalRegistros.value / limit.value))

        // --- FUNÇÕES ---

        const carregarOperadoras = async () => {
            loading.value = true
            try {
                const params = { page: page.value, limit: limit.value, search: search.value }
                const res = await axios.get('http://127.0.0.1:8000/api/operadoras', { params })
                operadoras.value = res.data.data
                totalRegistros.value = res.data.meta.total
                page.value = res.data.meta.page
            } catch (error) {
                console.error("Erro API:", error)
                alert("Erro ao buscar operadoras.")
            } finally {
                loading.value = false
            }
        }

        const carregarGrafico = async () => {
            try {
                const res = await axios.get('http://127.0.0.1:8000/api/estatisticas')
                const dados = res.data.distribuicao_uf.slice(0, 10)
                new Chart(document.getElementById('graficoEstados'), {
                    type: 'bar',
                    data: {
                        labels: dados.map(d => d.uf || 'N/D'),
                        datasets: [{
                            label: 'Total Despesas (R$)',
                            data: dados.map(d => d.total),
                            backgroundColor: '#3498db'
                        }]
                    }
                })
            } catch (e) { console.error("Erro Gráfico:", e) }
        }

        // --- NOVA LÓGICA DE DETALHES ---
        const abrirDetalhes = async (op) => {
            operadoraSelecionada.value = op
            modalAberto.value = true
            loadingDetalhes.value = true
            historico.value = [] // Limpa anterior

            try {
                // Chama a rota que criamos no backend: /api/operadoras/{cnpj}/despesas
                const res = await axios.get(`http://127.0.0.1:8000/api/operadoras/${op.cnpj}/despesas`)
                historico.value = res.data
            } catch (error) {
                console.error("Erro ao carregar detalhes:", error)
                alert("Erro ao carregar histórico de despesas.")
            } finally {
                loadingDetalhes.value = false
            }
        }

        const fecharModal = () => {
            modalAberto.value = false
        }

        const mudarPagina = (p) => { page.value = p; carregarOperadoras() }
        const buscar = () => { page.value = 1; carregarOperadoras() }

        onMounted(() => {
            carregarOperadoras()
            carregarGrafico()
        })

        return {
            operadoras, page, totalPaginas, totalRegistros, search, loading,
            mudarPagina, buscar,
            // Retornando os novos itens
            modalAberto, operadoraSelecionada, historico, loadingDetalhes, abrirDetalhes, fecharModal
        }
    }
}).mount('#app')