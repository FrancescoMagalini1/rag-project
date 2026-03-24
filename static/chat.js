import { marked } from "https://cdn.jsdelivr.net/npm/marked/lib/marked.esm.js";

function addResponse(e) {
  try {
    const response = e.detail.xhr.response;
    const question = e.detail.requestConfig.formData.get("message");
    const responseMessage = marked.parse(response, { breaks: true });
    console.log(question, responseMessage);
    content = document.getElementById("content");
    const questionDiv = document.createElement("div");
    questionDiv.className = "message question";
    questionDiv.textContent = question;

    const answerDiv = document.createElement("div");
    answerDiv.className = "message answeranswer";
    answerDiv.innerHTML = responseMessage;

    content.appendChild(questionDiv);
    content.appendChild(answerDiv);
    form.querySelector("textarea").value = "";
  } catch (error) {
    console.error(error);
  }
}

function formatMessages() {
  const answers = document.querySelectorAll("div.to-format");
  console.log(answers);
  for (const answer of answers) {
    const text = answer.innerText;
    console.log(text);
    answer.innerHTML = marked.parse(text, { breaks: true });
    answer.classList.remove("to-format");
  }
}

const form = document.querySelector("form");
if (form) {
  form.addEventListener("htmx:afterRequest", addResponse);
  formatMessages();
}

const testMessage = `"Here is a summary of a typical Bosch Non-Disclosure Agreement (NDA), based on the retrieved context snippets from similar agreements:\n\n---\n\n### Summary of Bosch Non-Disclosure Agreement (NDA)\n1. Purpose:\n - The NDA is established to facilitate discussions between Bosch (or its subsidiaries/affiliates) and another party (e.g., a supplier, partner, or collaborator) for evaluating a potential business relationship.\n - It governs the exchange of confidential, proprietary, or trade secret information during these discussions.\n\n2. Parties Involved:\n - The agreement is mutual, meaning both Bosch and the other party (e.g., a supplier or partner) are bound by its terms.\n - The parties are referred to as the "Disclosing Party" (the one sharing confidential information) and the "Receiving Party" (the one receiving it).\n\n3. Key Definitions:\n - Confidential Information: Includes any non-public, proprietary, or sensitive information shared between the parties, such as technical data, business strategies, trade secrets, or intellectual property.\n - Purpose: The specific business objective or project for which the information is being shared (e.g., evaluating a partnership, product development, or supply chain collaboration).\n\n4. Obligations of the Receiving Party:\n - The Receiving Party must:\n - Use the confidential information only for the agreed Purpose.\n - Protect the information with at least the same degree of care as it uses for its own confidential information (but no less than a reasonable standard).\n - Not disclose the information to third parties without prior written consent.\n - Limit access to the information to employees, agents, or representatives who need to know for the Purpose and are bound by confidentiality obligations.\n\n5. Term and Duration:\n - The agreement specifies:\n - An Effective Date (when the NDA becomes active).\n - A Period for Exchange of Information (the duration during which confidential information may be shared).\n - A Period of Confidentiality (how long the Receiving Party must keep the information confidential, often 2–5 years or longer, depending on the sensitivity of the information).\n\n6. Exclusions:\n - The Receiving Party is not obligated to protect information that:\n - Was already lawfully known to the Receiving Party before disclosure.\n - Becomes publicly available through no fault of the Receiving Party.\n - Is lawfully obtained from a third party without confidentiality restrictions.\n - Is independently developed by the Receiving Party without reliance on the Disclosing Party’s confidential information.\n\n7. Return or Destruction of Information:\n - Upon request, the Receiving Party must return or destroy all confidential information and certify compliance with this obligation.\n\n8. No License or Ownership Transfer:\n - The NDA does not grant any rights, title, or interest in the confidential information to the Receiving Party. All intellectual property remains the property of the Disclosing Party.\n\n9. Termination:\n - The agreement may be terminated by either party with written notice, but the confidentiality obligations survive termination.\n\n10. Miscellaneous Provisions:\n - Governing Law: The agreement is typically governed by the laws of a specific jurisdiction (e.g., Germany, where Bosch is headquartered, or another relevant country).\n - Entire Agreement: The NDA supersedes all prior agreements or understandings related to its subject matter.\n - Amendments: Any changes must be made in writing and signed by both parties.\n - No Obligation to Proceed: The NDA does not obligate either party to enter into a business relationship; it only protects the shared information.\n\n11. Signatures:\n - The agreement must be signed by authorized representatives of both parties to be enforceable.\n\n---\n\n### Key Takeaways\n- The Bosch NDA is a mutual agreement designed to protect sensitive information shared during business discussions.\n- It imposes strict confidentiality obligations on the Receiving Party, including limitations on use, disclosure, and access.\n- The agreement ensures that Bosch’s intellectual property and trade secrets remain protected, even if no formal business relationship is established."`;

function test() {
  try {
    content = document.getElementById("content");
    const questionDiv = document.createElement("div");
    questionDiv.className = "message question";
    questionDiv.textContent = "My question";

    const answerDiv = document.createElement("div");
    answerDiv.className = "message answer";
    answerDiv.innerHTML = marked.parse(testMessage, { breaks: true });

    content.appendChild(questionDiv);
    content.appendChild(answerDiv);
  } catch (error) {
    console.error(error);
  }
}
