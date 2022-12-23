

//const API = "http://localhost:8000";
const REFRESH = 1000;

//const API = await fetch("/host-backend").then(response => response.text());

class BackEnd {
    #data;

    constructor() {
        this.#data = null;
    }

    async getData() {
        if (!this.#data) {
            this.#data = await fetch("/_config").then(async function(response) {
                if (!response.ok) {
                    throw new Error("HTTP status " + response.status);
                }
                const data = await response.json();
                console.log(data)
                return data
            });
        };
        return this.#data
    }

    async getHost() {
        const data = await this.getData();
        return data.backend_url
    } 
}

const backend = new BackEnd();

async function queryApi(route, method="GET") {
    const host = await backend.getHost()
    console.log(`Querying ${host + route}`)
    let data = await fetch(
        host + route,
        {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'accept': 'application/json',
            }
        }
    ).then(response => {
        return response.json()
    });
    console.log(data)
    return data
}

function getVariant(status) {
    return {
        success: "success", run: "warning", fail: "danger", null: "dark"
    }[status]
}

function getStatus(status) {
    // Turn status more readable
    return {
        success: "Success", 
        run: "Running", 
        fail: "Failed", 
        null: "Not run", 
        terminate: "Terminated",
        crash: "Crashed",
        inaction: "Did nothing"
    }[status]
}

export { REFRESH, queryApi, getVariant, getStatus };