document.addEventListener('DOMContentLoaded', function () {
    atualizarData();
    adminLoader();
    highlightActiveNavbarItem();
    exibirModal();
    exibirMensagemPersonalizada();
    setupFormListeners();
    sendCachedData();
});

// Add focus event listeners to all input fields to ensure they scroll into view.
document.querySelectorAll('input').forEach(input => {
  input.addEventListener('focus', scrollToView);
});

const enviarBtn = document.getElementById('enviar-btn');
const camposDoFormulario = document.querySelectorAll('input, select');

// Disable the send button shortly after click to prevent multiple submissions.
if (enviarBtn) {
    enviarBtn.addEventListener('click', function () {
        setTimeout(function () {
            enviarBtn.disabled = true;
        }, 100);
    });

    camposDoFormulario.forEach(function (campo) {
        campo.addEventListener('input', function () {
            enviarBtn.disabled = false;
        });
    });
}

// Modify admin-specific links if the user is an administrator.
function adminLoader() {
    var userContainer = document.getElementById('username-link')
    if (typeof isAdmin !== 'undefined' && isAdmin) {
        if (isAdmin === true) {
            userContainer.setAttribute('href', "/admin")

        }
    }
}

// Check server availability.
function checkServerAvailability() {
    return fetch('/ping')
        .then(response => response.ok ? true : false)
        .catch(() => false);
}

// Scroll the active element smoothly into view after a delay.
function scrollToView(event) {
    var activeElement = event.target;
    setTimeout(() => {
        activeElement.scrollIntoView({behavior: 'smooth', block: 'center'});
    }, 300);
}

// Set up event listeners for forms to handle submissions and interact with the server.
function setupFormListeners() {
    document.querySelectorAll('form.dados').forEach(function (form) {
        form.addEventListener('submit', function (event) {
            event.preventDefault();
            var formData = new FormData(this);
            formData.append('formulario_id', form.getAttribute('id'));

            sendDataToServer('/processar_formulario', formData, 'POST')
                .then(({ message, type }) => {
                    exibirMensagemFlash(message, type);
                    console.log(message);
                    limparFormulario(form.getAttribute('id'));
                    showHiddenDiv(['observacoes-div', 'container-destino'], ['add']);
                })
                .catch(error => {
                    salvarNoIndexDB({ url: '/processar_formulario', data: formDataToObject(formData) });
                    exibirMensagemFlash('Dados armazenados. Eles serão enviados quando a conexão for restabelecida.', 'info');
                    console.log(error);
                    limparFormulario(form.getAttribute('id'));
                    showHiddenDiv(['observacoes-div', 'container-destino'], ['add']);
                });
        });
    });
    document.querySelectorAll('form.edit, form.delete').forEach(function (form) {
        form.addEventListener('submit', function (event) {
            event.preventDefault();
            var formData = new FormData(this);
            formData.append('formulario_id', form.getAttribute('id'));

            sendDataToServer('/processar_formulario', formData, form.getAttribute('method'))
                .then(({ message, type }) => {
                    $('.modal').modal('hide');
                    exibirMensagemFlash(message, type);
                    console.log(message);
                    $('#reload-table').click();
                })
                .catch(error => {
                    $('.modal').modal('hide');
                    exibirMensagemFlash('Ocorreu um erro. Tente novamente mais tarde', 'error');
                    console.log(error);
                });
        });
    });
}

// Convert FormData into a simple object.
function formDataToObject(formData) {
    var formDataObject = {};
    formData.forEach(function(value, key){
        formDataObject[key] = value;
    });
    return formDataObject;
}

// Send form data to server and handle the response.
function sendDataToServer(url, formData, method) {
    if (method == 'GET') {
        return fetch(url, { method: method}).then(response => response.json());
    } else {
        return fetch(url, { method: method, body: formData }).then(response => response.json());
    };
}

function lastKm(placaField, km, exitField) {
    placaValue = document.getElementById(placaField).value;
    kmField = document.getElementById(km);
    exitChecked = document.getElementById(exitField).checked;

    if (placaValue != 'SEM-PLACA') {
        checkServerAvailability()
            .then(serverAvailable => {
                if (serverAvailable) {
                    sendDataToServer('/api/last_km?placa[value]=' + placaValue, null, 'GET')
                    .then(({ message, last_km }) => {
                        console.log(message);
                        if (message == 'km no needed') {
                            kmField.querySelector('input').required = false
                            kmField.classList.add('hidden');
                        } else {
                            kmField.classList.remove('hidden');
                            kmField.querySelector('input').required = true
                            if (exitChecked) {
                                kmField.querySelector('input').value = last_km
                            };
                        }
                    })
                    .catch(error => {
                        console.log(error);
                        kmField.classList.remove('hidden');
                        kmField.querySelector('input').required = true
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
}

// Open IndexedDB to store data if the server cannot be reached.
function openIndexedDB() {
    return new Promise((resolve, reject) => {
        var request = indexedDB.open("formularioDB", 1);
        request.onupgradeneeded = function (event) {
            var db = event.target.result;
            if (!db.objectStoreNames.contains("formularioStore")) {
                db.createObjectStore("formularioStore", { keyPath: "id", autoIncrement: true });
            }
        };
        request.onsuccess = function (event) {
            resolve(event.target.result);
        };

        request.onerror = function (event) {
            reject("Erro ao abrir o banco de dados: " + event.target.errorCode);
        };
    });
}

// Store unsent data in IndexedDB and log success or error.
function salvarNoIndexDB(data) {
    openIndexedDB()
        .then(db => {
            var transaction = db.transaction(["formularioStore"], "readwrite");
            var objectStore = transaction.objectStore("formularioStore");
            objectStore.add(data);
            return transaction.complete;
        })
        .then(() => console.log('Dados salvos no IndexedDB com sucesso.'))
        .catch(error => console.error('Erro ao salvar no IndexedDB:', error));
}

// Send cached data from IndexedDB to server when the connection is available.
function sendCachedData() {
    openIndexedDB()
        .then(db => {
            return new Promise((resolve, reject) => {
                var objectStore = db.transaction(["formularioStore"], "readwrite").objectStore("formularioStore");
                var request = objectStore.getAll();

                request.onsuccess = function(event) {
                    resolve(event.target.result);
                };

                request.onerror = function(event) {
                    reject("Erro ao obter dados em cache: " + event.target.errorCode);
                };
            });
        })
        .then(cachedData => {
            if (cachedData && cachedData.length > 0) {
                checkServerAvailability()
                    .then(serverAvailable => {
                        if (serverAvailable) {
                            sendCachedDataRecursiveStep(cachedData, 0);
                        }
                    })
                    .catch(error => {
                        console.error('Erro ao verificar a disponibilidade do servidor:', error);
                    });
            }
        })
        .catch(error => console.error('Erro ao enviar dados em cache:', error));
}

// Recursive function to send each item of cached data to the server.
function sendCachedDataRecursiveStep(cachedData, index) {
    if (index < cachedData.length) {
        var item = cachedData[index];
        var formData = new FormData();

        for (var key in item.data) {
            formData.append(key, item.data[key]);
        }

        formData.append('formulario_id', item.formulario_id);

        sendDataToServer(item.url, formData, 'POST')
            .then(({ message, type }) => {
                exibirMensagemFlash(message, type);
                return openIndexedDB();
            })
            .then(db => {
                var transaction = db.transaction(["formularioStore"], "readwrite");
                var objectStore = transaction.objectStore("formularioStore");
                objectStore.delete(item.id);
                return transaction.complete;
            })
            .then(() => {
                sendCachedDataRecursiveStep(cachedData, index + 1);
            })
            .catch(error => {
                exibirMensagemFlash(error.message, 'error');
            });
    }
}

// setup fields to include dynamic options
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

        filterAndDisplayOptions(valorAtual, all_visitantes, visitante, visitanteOptions);
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

        filterAndDisplayOptions(valorAtual, all_motoristas, motorista, motoristaOptions);
    });

    motorista.addEventListener('blur', function() {
        setTimeout(function() {
            motoristaOptions.classList.remove('show');
        }, 300);
    });
}

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

        filterAndDisplayOptions(valorAtual, all_placas, placa, placaOptions);
    });

    placa.addEventListener('blur', function() {
        setTimeout(function() {
            placaOptions.classList.remove('show');
        }, 300);
    });
}


// setup the field "Placa" to correspond to a specific pattern
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

function setupOnlyLetters(idElement) {
    element = document.getElementById(idElement);
    element.value = element.value.toUpperCase().replace(/[0-9]/g, '');
}

// filters and organize dynamic options based on the user input
function filterAndDisplayOptions(valorAtual, allOptions, inputField, optionsContainer) {
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

// Confirm the intention to clear the form data with a confirmation dialog.
function confirmarLimpeza(form) {
    var confirmar = confirm("Tem certeza que deseja limpar tudo?");
    if (confirmar) {
        limparFormulario(form);
    }
}

// Resets the form fields and updates the date to the current date.
function limparFormulario(form) {
    var formulario = document.getElementById(form);
    formulario.reset();
    atualizarData();
}

// Validates and formats the vehicle plate input.
function verificarPlaca() {
    var placaElement = document.getElementById("placa");
    var kmElement = document.getElementById("quilometragem");
    var descricaoDiv = document.getElementById("div-descricao");
    var descricaoElement = document.getElementById("descricao");

    if (placaElement.value == "SEM-PLACA") {
        placaElement.removeAttribute('pattern');
        placaElement.maxLength = "9";
        kmElement.required = false;
        descricaoDiv.classList.remove('hidden')
        descricaoElement.required = true;
    } else {
        placaElement.pattern = "[A-Z]{3}-\\d[A-j0-9]\\d{2}"
        placaElement.maxLength = "8"
        kmElement.required = true;
        descricaoDiv.classList.add('hidden')
        descricaoElement.required = false;
    }
}

// Formats input values as currency.
function myCurrency(e) {
    var x = document.getElementById("preco");
    var currentVal = x.value;

    document.getElementById("preco").addEventListener('input', function (e) {
        this.value = this.value.replace(/[^0-9]/g, '');
    });

    if (currentVal == "") {
        x.value = "0,00";
    } else {
        var num = currentVal.replace(/,/g, '').replace(/^0+/, '');
        if(num == "") num = "0";
        var len = num.length;
        if(len == 1) num = "0,0" + num;
        else if(len == 2) num = "0," + num;
        else num = num.slice(0, len-2) + "," + num.slice(len-2);
        x.value = num;
    }
}

// Highlights the navbar item that corresponds to the current page URL.
function highlightActiveNavbarItem() {
    let currentUrl = window.location.href;
    let navbarItems = document.querySelectorAll(".navbar-nav .nav-link");
    navbarItems.forEach((navbarItem) => {
        if (currentUrl.includes(navbarItem.href)) {
            navbarItem.classList.add("active");
        }
    })
}

// Updates the date/time input field to today's date in ISO format.
function atualizarData() {
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

// Displays a personalized greeting based on the current time of day.
function exibirMensagemPersonalizada() {
    var agora = new Date();
    var hora = agora.getHours();
    var mensagem = hora < 12 ? "Bom dia, " : hora < 18 ? "Boa tarde, " : "Boa noite, ";
    var elementoMensagem = document.getElementById("welcome_message");
    if (elementoMensagem) {
        elementoMensagem.innerHTML = mensagem + elementoMensagem.innerHTML;
    }
}

// Displays and manages flash messages in a modal.
function exibirMensagemFlash(mensagem, tipo) {
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
        fecharModal(modal.getAttribute("id"));
    }, 3000);
    window.addEventListener('click', function (event) {
        if (event.target === modal) {
            fecharModal(modal.getAttribute("id"));
        }
    });
}

// Displays a modal if there are any flash messages.
function exibirModal() {
    var modal = document.getElementById('myModal');
    var flashes = document.querySelector('.flashes');
    if (flashes && flashes.children.length > 0) {
        modal.classList.add('show');
        setTimeout(function () {
            fecharModal(odal.getAttribute("id"));;
        }, 3000);
        window.addEventListener('click', function (event) {
            if (event.target === modal) {
                fecharModal(modal.getAttribute("id"));;
            }
        });
    }
}

// Closes the modal with a fade-out effect.
function fecharModal(modal_id) {
    var modal = document.getElementById(modal_id);
    modal.classList.add('fade-out');
    setTimeout(function () {
        modal.classList.remove('show', 'fade-out');
    }, 200);
}

// Control the appearing/disappearing style of any div
function showHiddenDiv(element, option) {
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


// Shows only the options of container-destino that corresponds to the categoria's option
function showEnterExitOptions(categoria) {
    var allOptions = document.getElementsByName('destino');
    var allOptionsLabel = document.querySelectorAll('.label-destino');
    var filteredOptions = document.querySelectorAll(categoria);
    var outrosOption = document.getElementById('label-outros');

    showHiddenDiv(['observacoes-div', 'container-destino'], ['add', 'remove']);

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
