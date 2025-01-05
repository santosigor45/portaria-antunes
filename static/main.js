// dispara quando o DOM estiver completamente carregado
document.addEventListener('DOMContentLoaded', function () {
    updateDate();
    adminLoader();
    highlightActiveNavbarItem();
    showModal();
    showCustomMessage();
    setupFormListeners();
    setupSendButtonBehavior();

    // adiciona event listeners de foco para todos os inputs, ativando a função scrollToView
    document.querySelectorAll('input').forEach(input => {
      input.addEventListener('focus', scrollToView);
    });
});

/*************************************************************/
/*                   ENVIO DE FORMULARIO                     */
/*************************************************************/

// inicializa listeners em todos os formulários (edit, delete, dados)
function setupFormListeners() {
    document.querySelectorAll('form.edit, form.delete, form.dados').forEach(function (form) {
        form.addEventListener('submit', async function (event) {
            event.preventDefault();
            const formData = new FormData(this);
            const formId = form.getAttribute('id')
            const url = '/process_form/' +
                        (formId.startsWith('edit') ? 'edit/' :
                        formId.startsWith('delete') ? 'delete/' : 'send/') +
                        formId;

            submitFormData(url, formData, form, formId);
        });
    });
}


// envia dados do formulário ao servidor e lida com a resposta
function submitFormData(url, formData, form, formId) {
    sendDataToServer(url, formData, form.getAttribute('method'))
        .then(({ message, type }) => {
            if (url.includes('send')) {
                formReset(formId);
                showHiddenElement(['observacoes-div', 'container-destino'], ['add']);
            } else {
                $('.modal').modal('hide');
                $('#reload-table').click();
            }
            showFlashMessage(message, type);
        })
        .catch(error => {
            if (url.includes('send')) {
                showFlashMessage('Houve um erro. Por favor, verifique a conexão e tente novamente.', 'info');
            } else {
                $('.modal').modal('hide');
                showFlashMessage('Houve um erro. Por favor, verifique a conexão e tente novamente.', 'error');
            }
            console.log(error);
        });
}


// requisicao generica ao servidor, usando fetch
function sendDataToServer(url, formData, method = 'POST') {
    if (method === 'GET') {
        return fetch(url, { method }).then((response) => response.json());
    }
    return fetch(url, { method, body: formData }).then((response) => response.json());
}

/*************************************************************/
/*               CONFIGURACOES DE FORMULARIO                 */
/*************************************************************/

// atualiza o campo de data para a data atual no formato ISO (yyyy-mm-dd)
function updateDate() {
    var today = new Date();
    var offset = today.getTimezoneOffset() * 60000;
    var localISOTime = (new Date(today - offset)).toISOString();

    dataElement = document.getElementById('data')
    timeElement = document.getElementById('hora')

    if (dataElement) {
        dataElement.value = localISOTime.split('T')[0];
        timeElement.value = localISOTime.split('T')[1].slice(0, -8);
    }
}


// configura campo de input para motorista, exibindo opções filtradas
function setupMotoristaInput(field = 'motorista') {
    var motorista = document.getElementById(field);

    motorista.addEventListener('input', function() {
        setupOnlyLetters(field);
    });

    setupMotoristaOptions(field);
}

function setupMotoristaOptions(field) {
    var motoristaOptions = document.getElementById('motoristaOptions');

    if (!motoristaOptions) {
        return
    }

    var motorista = document.getElementById(field);
    var all_motoristas = Array.from(motoristaOptions.children);

    motorista.addEventListener('input', function() {
        var valorAtual = motorista.value;
        motoristaOptions.innerHTML = '';

        displayOptions(valorAtual, all_motoristas, motorista, motoristaOptions);
    });

    motorista.addEventListener('blur', function() {
        setTimeout(function() {
            motoristaOptions.classList.remove('show');
        }, 300);
    });
}


// configura campo de input para placa, exibindo opções filtradas e formatando a digitacao
function setupPlacaInput(field = 'placa') {
    var placa = document.getElementById(field);

    placa.addEventListener('input', function() {
        placa.value = placa.value.toUpperCase();
        setupPlacaPattern(field);
    });

    setupPlacaOptions(field);
}

function setupPlacaOptions(field) {
    var placaOptions = document.getElementById('placaOptions');

    if (!placaOptions) {
        return
    }

    var placa = document.getElementById(field);
    var all_placas = Array.from(placaOptions.children);

    placa.addEventListener('input', function() {
        var valorAtual = placa.value;
        placaOptions.innerHTML = '';

        displayOptions(valorAtual, all_placas, placa, placaOptions);
    });

    placa.addEventListener('blur', function() {
        setTimeout(function() {
            placaOptions.classList.remove('show');
        }, 300);
    });
}

function setupPlacaPattern(field) {
    var placa = document.getElementById(field);
    var valorAtual = placa.value;

    if (valorAtual.length <= 3) {
        placa.value = valorAtual.replace(/[^A-Z]/g, '');
    }
    else if (valorAtual.length === 4 && valorAtual.charAt(3) !== '-' && valorAtual.charAt(3) >= '0' && valorAtual.charAt(3) <= '9') {
        placa.value = valorAtual.substring(0, 3) + '-' + valorAtual.charAt(3);
    }
    else if (valorAtual.length === 6) {
        placa.value = valorAtual.substring(0, 5) + valorAtual.charAt(5).replace(/[^A-J0-9]/g, '');
    }
    else if (valorAtual.length >= 7) {
        placa.value = valorAtual.substring(0, 6) + valorAtual.charAt(6).replace(/[^0-9]/g, '') + valorAtual.charAt(7).replace(/[^0-9]/g, '');
    }
    else if (valorAtual.length === 4) {
        placa.value = valorAtual.slice(0, -1);
    }

    placa.addEventListener('keydown', function(event) {
        var valorAtual = placa.value;

        if (event.key === 'Backspace') {
            if (valorAtual.length === 5) {
                placa.value = valorAtual.slice(0, -1);
            }
        }
    });
}


// configura campo de input para visitantes, exibindo opcoes filtradas
function setupVisitantesInput(visitor, doc, company, visitorsList) {
    var visitante = document.getElementById(visitor);
    var visitanteOptions = document.getElementById('visitanteOptions');
    var documento = document.getElementById(doc);
    var empresa = document.getElementById(company);

    if (!visitanteOptions) {
        return
    }

    var all_visitantes = Array.from(visitanteOptions.children);
    var all_fields = Array.from(visitorsList);

    visitante.addEventListener('input', function() {
        setupOnlyLetters(visitor);
        var valorAtual = visitante.value;
        visitanteOptions.innerHTML = '';

        displayOptions(valorAtual, all_visitantes, visitante, visitanteOptions);
    });

    visitante.addEventListener('blur', function() {
        setTimeout(function() {
            visitanteOptions.classList.remove('show');
            for (let i = 0; i < all_visitantes.length; i++) {
                if (visitante.value == all_fields[i]['nome']) {
                    documento.value = all_fields[i]['documento'];
                    documento.readOnly = true;
                    documento.style = 'background-color: #D3D3D3'
                    empresa.value = all_fields[i]['empresa'];
                    empresa.readOnly = true;
                    empresa.style = 'background-color: #D3D3D3'
                    break
                } else {
                    documento.value = '';
                    documento.readOnly = false;
                    documento.style = 'background-color: white'
                    empresa.value = '';
                    empresa.readOnly = false;
                    empresa.style = 'background-color: white'
                }
            }
        }, 300);
    });
}


// filtra as opcoes e exibe na tela, baseado no valor atual do input
function displayOptions(valorAtual, allOptions, inputField, optionsContainer) {
    optionsContainer.innerHTML = '';

    if (valorAtual.length === 0) {
        optionsContainer.classList.remove('show');
        return;
    }

    const valorAtualUpper = valorAtual.toUpperCase();
    let matches = [];

    for (const option of allOptions) {
        const optionValue = option.innerText.toUpperCase();

        if (optionValue.includes(valorAtualUpper)) {
            const index = optionValue.indexOf(valorAtualUpper);
            matches.push({option, index});
        }
    }

    matches.sort((a, b) => a.index - b.index);

    for (const match of matches) {
        const clonedOption = match.option.cloneNode(true);
        optionsContainer.appendChild(clonedOption);

        clonedOption.addEventListener('click', function() {
            inputField.value = clonedOption.innerText.split(' |')[0];
            optionsContainer.classList.remove('show');
        });
    }

    optionsContainer.classList.add('show');
}


// mostra apenas as opcoes de destino que correspondem a categoria selecionada
function showEnterExitOptions(categoria) {
    var allOptions = document.getElementsByName('destino');
    var allOptionsLabel = document.querySelectorAll('.label-destino');
    var filteredOptions = document.querySelectorAll(categoria);
    var outrosOption = document.getElementById('label-outros');

    showHiddenElement(['observacoes-div', 'container-destino'], ['add', 'remove']);

    for (var i = 0; i < allOptions.length; i++) {
        allOptions[i].checked = false;
        if (allOptionsLabel[i].id != outrosOption.id) {
            allOptionsLabel[i].classList.add('hidden');
        }
    }
    for (var i = 0; i < filteredOptions.length; i++) {
        filteredOptions[i].classList.remove('hidden')
    }
}


// desabilita o botao de envio por um curto período para evitar envios duplicados
function setupSendButtonBehavior() {
    const submitButton = document.getElementById('enviar-btn');
    const formFields = document.querySelectorAll('input, select');

    if (!submitButton) return;

    submitButton.addEventListener('click', () => {
        setTimeout(() => {
            submitButton.disabled = true;
        }, 100);
    });

    formFields.forEach((field) => {
        field.addEventListener('input', () => {
            submitButton.disabled = false;
        });
    });
}

/*************************************************************/
/*                VERIFICACOES DE FORMULARIO                 */
/*************************************************************/

// formata o texto digitado em um campo de placa (AAA-0A00).
function validateLicensePlate() {
    var placaElement = document.getElementById("placa");
    var descricaoDiv = document.getElementById("div-descricao");
    var descricaoElement = document.getElementById("descricao");

    if (placaElement.value == "SEM-PLACA") {
        placaElement.removeAttribute('pattern');
        placaElement.maxLength = "9";
        descricaoDiv.classList.remove('hidden')
        descricaoElement.required = true;
    } else {
        placaElement.pattern = "[A-Z]{3}-\\d[A-j0-9]\\d{2}"
        placaElement.maxLength = "8"
        descricaoDiv.classList.add('hidden')
        descricaoElement.required = false;
    }
}

/*************************************************************/
/*                          APIs                             */
/*************************************************************/

// retorna o ultimo km registrado da placa informada
function retrieveMileage(placaField, km, exitField) {
    placaValue = document.getElementById(placaField).value;
    kmField = document.getElementById(km);
    exitChecked = document.getElementById(exitField).checked;

    if (placaValue != 'SEM-PLACA') {
        if (exitChecked) {
            checkServerAvailability()
                .then(serverAvailable => {
                    if (serverAvailable) {
                        sendDataToServer('/api/retrieve_mileage?placa[value]=' + placaValue, null, 'GET')
                        .then(({ message, retrieved_mileage }) => {
                            console.log(message);
                            if (message == 'km no needed') {
                                kmField.querySelector('input').required = false
                            };
                            kmField.querySelector('input').value = retrieved_mileage
                        })
                        .catch(error => {
                            console.log(error);
                            return
                        });
                    }
                })
            .catch(error => {
                console.error('Erro ao verificar a disponibilidade do servidor:', error);
            });
        } else {
            return
        };
    } else {
        return
    };
}


// retorna a placa e o documento ao colocar o nome do visitante
function loadVisitorData(placaField, visitor, exitField) {
    placaValue = document.getElementById(placaField).value;
    visitorField = document.getElementById(visitor);
    exitChecked = document.getElementById(exitField).checked;

    if (placaValue != 'SEM-PLACA') {
        if (exitChecked) {function loadVisitorData(placaField, visitor, exitField) {
            placaValue = document.getElementById(placaField).value;
            visitorField = document.getElementById(visitor);
            exitChecked = document.getElementById(exitField).checked;

            if (placaValue != 'SEM-PLACA') {
                if (exitChecked) {
                    checkServerAvailability()
                        .then(serverAvailable => {
                            if (serverAvailable) {
                                sendDataToServer('/api/load_visitor_data?placa[value]=' + placaValue, null, 'GET')
                                .then(({ message, visitor_name }) => {
                                    console.log(message);
                                    visitorField.value = visitor_name;
                                    visitorField.readOnly = true;
                                    visitorField.focus();
                                    setTimeout( function() {
                                        visitorField.blur();
                                    }, 300);
                                    visitorField.readOnly = false;
                                })
                                .catch(error => {
                                    console.log(error);
                                    return
                                });
                            }
                        })
                    .catch(error => {
                        console.error('Erro ao verificar a disponibilidade do servidor:', error);
                    });
                } else {
                    return
                };
            } else {
                return
            };
        }
        checkServerAvailability()
            .then(serverAvailable => {
                if (serverAvailable) {
                    sendDataToServer('/api/load_visitor_data?placa[value]=' + placaValue, null, 'GET')
                    .then(({ message, visitor_name }) => {
                        console.log(message);
                        visitorField.value = visitor_name;
                        visitorField.readOnly = true;
                        visitorField.focus();
                        setTimeout( function() {
                            visitorField.blur();
                        }, 300);
                        visitorField.readOnly = false;
                    })
                    .catch(error => {
                        console.log(error);
                        return
                    });
                }
            })
            .catch(error => {
                console.error('Erro ao verificar a disponibilidade do servidor:', error);
            });
            } else {
                return
            };
    } else {
        return
    };
}

/*************************************************************/
/*                        ESTETICA                           */
/*************************************************************/

// faz a rolagem suave ate o elemento focado com um atraso
function scrollToView(event) {
    var activeElement = event.target;
    setTimeout(() => {
        activeElement.scrollIntoView({behavior: 'smooth', block: 'center'});
    }, 300);
}


// destaca o item do navbar correspondente a URL atual
function highlightActiveNavbarItem() {
    let currentUrl = window.location.href;
    let navbarItems = document.querySelectorAll(".navbar-nav .nav-link");
    navbarItems.forEach((navbarItem) => {
        if (currentUrl.includes(navbarItem.href)) {
            navbarItem.classList.add("active");
        }
    })
}


// exibe saudacao personalizada (bom dia, boa tarde, boa noite)
function showCustomMessage() {
    var agora = new Date();
    var hora = agora.getHours();
    var mensagem = hora < 12 ? "Bom dia, " : hora < 18 ? "Boa tarde, " : "Boa noite, ";
    var elementoMensagem = document.getElementById("welcome_message");
    if (elementoMensagem) {
        elementoMensagem.innerHTML = mensagem + elementoMensagem.innerHTML;
    }
}

/*************************************************************/
/*                        MODALS                             */
/*************************************************************/

// abre o modal
function showModal() {
    var modal = document.getElementById('myModal');
    var flashes = document.querySelector('.flashes');
    if (flashes && flashes.children.length > 0) {
        modal.classList.add('show');
        setTimeout(function () {
            closeModal(odal.getAttribute("id"));;
        }, 3000);
        window.addEventListener('click', function (event) {
            if (event.target === modal) {
                closeModal(modal.getAttribute("id"));;
            }
        });
    }
}


// fecha o modal
function closeModal(modal_id) {
    var modal = document.getElementById(modal_id);
    modal.classList.add('fade-out');
    setTimeout(function () {
        modal.classList.remove('show', 'fade-out');
    }, 200);
}


// gerencia mensagens flash em uma modal
function showFlashMessage(mensagem, tipo) {
    var modal = document.getElementById('jsModal');
    modal.classList.add('show');
    var flash_content = document.getElementById('js-flash-content');
    var flash_text = document.getElementById('js-flash-text');
    flash_text.classList.add("flash-text-" + tipo);
    flash_content.classList.add("flash-" + tipo);
    flash_text.innerHTML = mensagem;
    setTimeout(function () {
        flash_text.classList.remove("flash-text-" + tipo);
        flash_content.classList.remove("flash-" + tipo);
        closeModal(modal.getAttribute("id"));
    }, 3000);
    window.addEventListener('click', function (event) {
        if (event.target === modal) {
            closeModal(modal.getAttribute("id"));
        }
    });
}

/*************************************************************/
/*                       PERMISSOES                          */
/*************************************************************/

// ajusta UI de links específicos se o usuário for administrador
function adminLoader() {
    var userContainer = document.getElementById('username-link')
    if (typeof isAdmin !== 'undefined' && isAdmin) {
        if (isAdmin === true) {
            userContainer.setAttribute('href', "/admin")

        }
    }
}

/*************************************************************/
/*                     QR CODE SCANNER                       */
/*************************************************************/

// abre o modal e configura o leitor de QR Code
function qrCodeReader() {
    let html5QrcodeScanner = new Html5QrcodeScanner("reader", { fps: 10, qrbox: 250 }, { rememberLastUsedCamera:true });
    $('#readerModal').modal('show');
    html5QrcodeScanner.render(onScanSuccess);
}


// preenche os dados retornados pelo leitor de QR Code
function onScanSuccess(decodedText, decodedResult) {
    const data = JSON.parse(decodedText);
    $('#placa').val(data['placa']);

    $('#html5-qrcode-button-camera-stop').click()
    $('#readerModal').modal('hide');
}

/*************************************************************/
/*                        UTILIDADES                         */
/*************************************************************/

// verifica disponibilidade do servidor atraves da rota /ping
function checkServerAvailability() {
    return fetch('/ping')
        .then(response => response.ok ? true : false)
        .catch(() => false);
}


// converte um objeto FormData para um objeto JS simples (key-value)
function formDataToObject(formData) {
    var formDataObject = {};
    formData.forEach(function(value, key){
        formDataObject[key] = value;
    });
    return formDataObject;
}


// exibe caixa de dialogo de confirmacao para limpeza de formulario
function confirmFormReset(form) {
    var confirmar = confirm("Tem certeza que deseja limpar tudo?");
    if (confirmar) {
        formReset(form);
    }
}


// reseta o formulario e atualiza a data para o dia atual
function formReset(form) {
    var formulario = document.getElementById(form);
    formulario.reset();
    updateDate();
}


// funcao generica que formata o input apenas com letras
function setupOnlyLetters(idElement) {
    element = document.getElementById(idElement);
    element.value = element.value.toUpperCase().replace(/[0-9]/g, '');
}


// funcao generica que controla o estilo hidden de qualquer elemento
function showHiddenElement(element, option) {
    var elementControlled = []
    for (var i = 0; i < element.length; i++) {
        elementControlled[i] = document.getElementById(element[i]);

        if (option.length <= 1) {
            if (option == 'add') {
                elementControlled[i].classList.add('hidden');
            } else if (option == 'remove') {
                elementControlled[i].classList.remove('hidden');
            }
        } else {
            if (option[i] == 'add') {
                elementControlled[i].classList.add('hidden');
            } else if (option[i] == 'remove') {
                elementControlled[i].classList.remove('hidden');
            }
        }
    }
}


// funcao generica que controla o atributo required de qualquer elemento
function removeAddRequired(element, option) {
    var elementControlled = []
    for (var i = 0; i < element.length; i++) {
        elementControlled[i] = document.getElementById(element[i]);

        if (option.length <= 1) {
            if (option == 'add') {
                elementControlled[i].required = true;
            } else if (option == 'remove') {
                elementControlled[i].required = false;
            }
        } else {
            if (option[i] == 'add') {
                elementControlled[i].required = true;
            } else if (option[i] == 'remove') {
                elementControlled[i].required = false;
            }
        }
    }
}
