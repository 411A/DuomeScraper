# DuomeScraper
<center>
  <img src="https://i.postimg.cc/W14rPY3b/Duolingo-In-Love-With-Anki.png" width="200" height="150">
</center>
This project scrapes the Italian words from the Duome website (https://duome.eu/vocabulary/en/it) using Playwright, then it downloads phonetics from GoogleTextToSpeech (gTTS) &amp; creates Anki flashcards.

# 🔰
<details>
  <summary>
    <b>How to run</b>
  </summary>

  <ol start="0">
  <li>Download <code>main.py</code> &amp; <code>requirements.txt</code> and put them inside a folder</li>
  <li>Create a virtual environment:
    <pre><code>python -m venv VEnv
    </code></pre>
  </li>
  <li>Activate virtual environment:
    <ul>
      <li>🪟 Windows CMD:
        <pre><code>VEnv\Scripts\activate
        </code></pre>
      </li>
      <li>🐧 Linux:
        <pre><code>source VEnv/bin/activate
        </code></pre>
      </li>
    </ul>
  </li>
  <li>Install dependencies:
    <pre><code>pip install -r requirements.txt
    </code></pre>
  </li>
  <li>Install playwright (⚠️ code uses Microsoft Edge browser, you can change that to chromium if you don't want to download <code>msedge</code>):
    <pre><code>playwright install &amp;&amp; playwright install msedge
    </code></pre>
  </li>
  <li>Read the code, you may need to personalize some variables, then run the <code>main.py</code></li>
</ol>

</details>

