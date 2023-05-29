let file = {
    pk: null,
    content: [],
    compiled_content: [],
}

function render_section(section_list, parent_div) {
    let parent = document.getElementById(parent_div);
    let sections = [];
    for (let i = 0; i < section_list.length; i++) {
        let subdiv = document.createElement('div');
        subdiv.setAttribute('class', 'subdiv')
        let id = parent_div + i;
        subdiv.setAttribute('id', id);
        subdiv.setAttribute('onclick', 'toggle_section("' + id + '")');
        let pre = document.createElement('pre');
        let code = document.createElement('code');
        code.innerText = section_list[i];
        pre.innerHTML = code.outerHTML;
        subdiv.innerHTML = pre.outerHTML;
        sections.push(subdiv.outerHTML);
    }
    parent.innerHTML = sections.join("");
}

function render_file(fileId) {
    const xhtml = new XMLHttpRequest();

    xhtml.open("GET", fileId, true);
    xhtml.send();

    xhtml.onload = function () {
        if (xhtml.status === 200) {
            file.pk = fileId;
            let parsed_response = JSON.parse(xhtml.responseText);
            console.log(parsed_response);
            file.content = parsed_response.content_by_section;
            file.compiled_content = parsed_response.compiled_by_section;
            render_section(file.content, "editor");
            render_section(file.compiled_content, "codeSnippet");
            find_and_mark_error();
        }
    }
}

function countBRTags(element) {
    let count = 0;

    if (element.tagName === "BR") {
        count++;
    }

    const children = element.children;
    for (let i = 0; i < children.length; i++) {
        count += countBRTags(children[i]);
    }

    return count;
}

function find_and_mark_error() {
    if (file.compiled_content.length === 0 ||
        !file.compiled_content[0].includes("syntax error")) {
        return;
    }
    const regex = /:(\d+):/g;
    let match = regex.exec(file.compiled_content[0]);
    let line_number = match[1];
    let editorSubdivs = document.getElementById("editor").children;
    let endl_cnt = 1;
    for (let i = 0; i < editorSubdivs.length; i++) {
        endl_cnt += countBRTags(editorSubdivs[i]);
        if (endl_cnt >= line_number) {
            editorSubdivs[i].style.backgroundColor = "rgba(255, 0, 0, 0.3)";// red
            editorSubdivs[i].style.color = "white";
            break;
        }
    }
}

function delete_fso(pk) {
    const xhtml = new XMLHttpRequest();
    if (file.pk === null) {
        xhtml.open("GET", "delete/" + pk, true);
    } else {
        xhtml.open("GET", "delete/" + pk + "/" + file.pk, true);
    }
    xhtml.send();

    xhtml.onload = function () {
        if (xhtml.status === 200) {
            document.getElementById("fso" + pk).remove();
            let parsed_response = JSON.parse(xhtml.responseText);
            console.log(parsed_response);
            let removed = parsed_response.removed;
            if (removed) {
                file.pk = null;
                file.content = [];
                file.compiled_content = [];
                render_section(file.content, "editor");
                render_section(file.compiled_content, "codeSnippet");
            }
        }
    }
}

function compile() {
    if (file.pk === null) {
        alert("Please select a file first");
    }
    const form = document.getElementById("compileForm");
    const formData = new FormData(form);
    console.log(formData);
    const xhtml = new XMLHttpRequest();
    xhtml.open("POST", "compile/" + file.pk, true);

    xhtml.send(formData);

    xhtml.onload = function () {
        if (xhtml.status === 200) {
            let parsed_response = JSON.parse(xhtml.responseText);
            file.compiled_content = parsed_response.compiled_by_section;
            render_section(file.compiled_content, "codeSnippet");
            find_and_mark_error();
        }
    }
}

function toggle_section(section_id) {
    let section = document.getElementById(section_id);
    // if height os not set to 50 set height to 50. remove height rule
    if (section.style.height !== "15px") {
        section.style.height = "15px";
    } else {
        section.style.height = "auto";
    }

}