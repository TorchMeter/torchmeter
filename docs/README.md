# Build documentation for your project

Due to the implementation details and documentation requirements varying from project to project, we can not provide a universal method for document construction.

However, we can provide some tool suggestions to help you quickly build your own document.

## `Sphinx`

> Official document: [Sphinx | Getting started](https://www.sphinx-doc.org/en/master/usage/quickstart.html)

<details>
<summary>❓ 𝐖𝐡𝐚𝐭 𝐢𝐬 𝐢𝐭</summary>

`Sphinx` is a powerful document generation tool mainly used for creating **professional** technical documents.

</details>

<details>
<summary>✨ 𝐇𝐢𝐠𝐡𝐥𝐢𝐠𝐡𝐭</summary>

- 📝 **Powerful typesetting**: Supports multiple formats such as `HTML`, `LaTeX`, and `PDF`, with elegant layout.
  
- 🔗 **Cross-reference**: Intelligent recognition and linking to improve document readability and maintenance efficiency.

- 👥 **Community support**: A large user community with rich document resources for convenient learning.

- 🔧 **Easy to extend**: Highly extensible and supports custom plugins to adapt to different needs.

   > <details>
   > <summary>🧩 𝙿̲𝚕̲𝚞̲𝚐̲𝚒̲𝚗̲ ̲𝚛̲𝚎̲𝚌̲𝚘̲𝚖̲𝚖̲𝚎̲𝚗̲𝚍̲𝚊̲𝚝̲𝚒̲𝚘̲𝚗̲</summary>
   > 
   > > More plugins refer to:  
   > > • [Sphinx Built-in Plugins](https://www.sphinx-doc.org/en/master/usage/extensions/index.html)    
   > > • [Sphinx Third-Party Plugins](https://github.com/sphinx-contrib/)   
   > > • [Awesome-sphinxdoc](https://github.com/yoloseem/awesome-sphinxdoc#extensions)    
   > > • [Sphinx-extensions](https://sphinx-extensions.readthedocs.io/en/latest/)
   > 
   > 1. `myst-parser`: Allow direct use of `Markdown` for writing and rendering > documents.
   > 2. `jupyter_sphinx`: Supports embedding and running `Jupyter` Notebook > content, suitable for documents containing data analysis and code examples.
   > 3. `sphinx.ext.todo`: Support adding `TODO` lists in documents for easy > task tracking and document management.
   > 4. `sphinx_copybutton`: Provide a one-click copy function for code blocks.
   > 5. `sphinx.ext.autodoc`: Automatically extract docstrings from `Python` > code and generate API documentation.
   > 6. `sphinx.ext.graphviz`: Supports `Graphviz` syntax and allows inserting > and displaying charts in documents.
   > 7.  `sphinx.ext.viewcode`: In the Sphinx project, allow direct use of > Markdown for writing and rendering documents.
   > 8.  `sphinx.ext.napoleon`: Supports Google and NumPy style docstrings and > automatically generates documentation from code comments.
   > 
   > </details>

- 🎨 **Rich in themes**: Multiple built-in themes and styles, and supports custom CSS.

   > <details>
   > <summary>🖼 𝚃̲𝚑̲𝚎̲𝚖̲𝚎̲ ̲𝚛̲𝚎̲𝚌̲𝚘̲𝚖̲𝚖̲𝚎̲𝚗̲𝚍̲𝚊̲𝚝̲𝚒̲𝚘̲𝚗̲</summary>
   > 
   > > More themes refer to [here](https://sphinx-themes.org/)
   > 
   > 1. [Furo](https://sphinx-themes.readthedocs.io/en/latest/sample-sites/furo/)
   > 
   >    ![](https://sphinx-themes.readthedocs.io/en/latest/preview-images/furo.jpg)
   > 
   > 2. [Book](https://sphinx-themes.readthedocs.io/en/latest/sample-sites/sphinx-book-theme/)
   > 
   >    ![](https://sphinx-themes.readthedocs.io/en/latest/preview-images/sphinx-book-theme.jpg)
   > 
   > 3. [PyData](https://sphinx-themes.readthedocs.io/en/latest/sample-sites/pydata-sphinx-theme/)
   >    
   >    ![](https://sphinx-themes.readthedocs.io/en/latest/preview-images/pydata-sphinx-theme.jpg)
   > 
   > 4. [Material](https://sphinx-themes.readthedocs.io/en/latest/sample-sites/sphinx-material/)
   > 
   >    ![](https://sphinx-themes.readthedocs.io/en/latest/preview-images/sphinx-material.jpg)
   > 
   > </details>

</details>

<details>
<summary>📌 𝐁𝐞𝐬𝐭 𝐏𝐫𝐚𝐜𝐭𝐢𝐜𝐞</summary>

1. 𝗘𝗻𝘃𝗶𝗿𝗼𝗻𝗺𝗲𝗻𝘁𝗮𝗹 𝗽𝗿𝗲𝗽𝗮𝗿𝗮𝘁𝗶𝗼𝗻

   ```bash
   pip install sphinx 
   pip install myst-parser # to support Markdown 
   ```

2. 𝗖𝗿𝗲𝗮𝘁𝗲 𝗮 `𝗦𝗽𝗵𝗶𝗻𝘅` 𝗽𝗿𝗼𝗷𝗲𝗰𝘁

    > clone this repo, and create a `Sphinx` project under the `docs` directory.

   - **Initial configuration**: set the project name, author, version, etc., and choose whether to separate the source directory and the build directory.

      ```bash
      # pwd: <Project_dir>/docs
      sphinx-quickstart
      ```

   - **Define the document structure**: edit the `source/index.rst` file and use the `.. toctree::` directive to organize the document.
   
   - **Write documentation**: Add or edit `.rst` or `.md` files in the `source` directory to write documentation content.

   - **Build and preview documents locally**: Use the following command in the project root directory, i.e. `<Project_dir>/docs` 
      
      ```bash
      # pwd: <Project_dir>/docs
      sphinx-autobuild source build/html
      ```

3. 𝗗𝗲𝗽𝗹𝗼𝘆 𝘁𝗵𝗲 `𝗦𝗽𝗵𝗶𝗻𝘅` 𝗽𝗿𝗼𝗷𝗲𝗰𝘁

   - **File hosting**: Push the document files to the project repository.
   - **Monitor document updates, automatically build and publish**
      - Register or log in to your [`Read the Docs`](https://readthedocs.org/) account.
      
      - Import GitHub projects into `Read the Docs` and set up project configs like `.readthedocs.yaml`.
      
      - Set up a webhook on `Read the Docs` to trigger automatic document building when `GitHub` code is updated.
   
     - Build and publish: Manually trigger a build on `Read the Docs` or wait for an automatic build. 
     
     - View documents using URL: after a successful build, the documentation will be published on `Read the Docs` and can be accessed through a provided URL.

4. 𝗠𝗮𝗶𝗻𝘁𝗮𝗶𝗻 𝗮𝗻𝗱 𝘂𝗽𝗱𝗮𝘁𝗲: write and update documents locally and push them to the project repository to trigger automatic builds on `Read the Docs`.

</details>

## `MkDocs`

> Official document: [MkDocs | Getting started](https://www.mkdocs.org/getting-started/)

<details>
<summary>❓ 𝐖𝐡𝐚𝐭 𝐢𝐬 𝐢𝐭</summary>

`MkDocs (Markdown Documents)` is a fast, simple and `Markdown`-based static **site generator** that's geared towards building project documentation quickly.    

</details>

<details>
<summary>✨ 𝐇𝐢𝐠𝐡𝐥𝐢𝐠𝐡𝐭</summary>

- 📖 **Easy for document generation**: Automatically extract code comments and convert them into `Markdown` documents.

- 📄 **Support and expand `Markdown`**: While making document writing easy and convenient, it provides a more beautiful page.

- 👥 `Community is active`.: Answers and suggestions can be found easily.

- 💪 **Diverse plugins**: Plugins can be installed to extend functions.

   > <details>
   > <summary>🧩 𝙿̲𝚕̲𝚞̲𝚐̲𝚒̲𝚗̲ ̲𝚛̲𝚎̲𝚌̲𝚘̲𝚖̲𝚖̲𝚎̲𝚗̲𝚍̲𝚊̲𝚝̲𝚒̲𝚘̲𝚗̲</summary>
   > 
   > > More plugins refer to [mkdocs/catalog](https://github.com/mkdocs/catalog)
   > 
   > 1. `mkdocs-multirepo-plugin`: Build documentation in multiple repos into > one site.
   > 
   > 2. `mkdocs-autolinks-plugin`: Automagically generates relative links > between markdown pages.
   > 
   > 3. `mkdocs-pdf-export-plugin`: Export content pages as PDF files.
   > 
   > 4.  `mkdocs-table-reader-plugin`: Enables a markdown tag like `{{ read_csv> (table.csv) }}` to directly insert various table formats into.
   > 
   > 5.  `mkdocs-awesome-pages-plugin`: Simplifies configuring page titles and > their order.
   > 
   > 6.  `mkdocs-encryptcontent-plugin`: Encrypt/decrypt markdown content with > AES.
   > 
   > 7.  `mkdocs-git-revision-date-plugin`: Add a last updated date to your site > pages.
   > 
   > </details>

- 🎨 **Rich in themes**: Provide diverse theme customization styles.

   > <details>
   > <summary>🖼 𝚃̲𝚑̲𝚎̲𝚖̲𝚎̲ ̲𝚛̲𝚎̲𝚌̲𝚘̲𝚖̲𝚖̲𝚎̲𝚗̲𝚍̲𝚊̲𝚝̲𝚒̲𝚘̲𝚗̲</summary>
   > 
   > > More themes refer to    
   > > • [MkDocs Themes](https://github.com/mkdocs/mkdocs/wiki/MkDocs-Themes)    
   > > • [mkdocs/catalog](https://github.com/mkdocs/catalog?tab=readme-ov-file#-theming)
   > 
   > - [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
   > 
   >    ![](https://raw.githubusercontent.com/squidfunk/mkdocs-material/master/.github/assets/screenshot.png)
   > 
   > - [Dracula](https://dracula.github.io/mkdocs/)
   >   
   >    ![](https://raw.githubusercontent.com/dracula/mkdocs/main/screenshot.png)
   > 
   > - [GitBook Theme](https://lramage.gitlab.io/mkdocs-gitbook-theme/)
   > 
   >    ![](https://camo.githubusercontent.com/0a856e406b0e0d4937c3dd8c10bcfdaa9dadd6f8baf87ee17e1749d016e493de/68747470733a2f2f6769746c61622e636f6d2f6c72616d6167652f6d6b646f63732d676974626f6f6b2d7468656d652f7261772f6d61737465722f696d672f73637265656e73686f742e706e67)
   > 
   > - [CustomMill](https://siphalor.github.io/mkdocs-custommill/#usage/)
   >   
   >    ![](https://github.com/Siphalor/mkdocs-custommill/raw/master/screenshot.png)
   > 
   > </details>

</details>

<details>
<summary>📌 𝐁𝐞𝐬𝐭 𝐏𝐫𝐚𝐜𝐭𝐢𝐜𝐞</summary>

1. 𝗘𝗻𝘃𝗶𝗿𝗼𝗻𝗺𝗲𝗻𝘁𝗮𝗹 𝗽𝗿𝗲𝗽𝗮𝗿𝗮𝘁𝗶𝗼𝗻

     ```bash
     pip install mkdocs
     ```

2. 𝗖𝗿𝗲𝗮𝘁𝗲 𝗮 `𝗠𝗸𝗗𝗼𝗰𝘀` 𝗽𝗿𝗼𝗷𝗲𝗰𝘁
   
   > clone this repo, and create a `Mkdocs` project under the `docs` directory.

   - **Initial configuration**: the command below will generate a `mkdocs.yml` configuration file under `<Project_dir>` and generate an `index.md` file under the `docs` folder.

      ```bash
      # pwd: <Project_dir>

      cd ..
      mkdocs <Project_dir>
      cd <Project_dir>
      ```
   
   - **Theme and Plugins configuration**: configure `mkdocs.yml` to customize the theme and plugins.

   - **Write documentation**: Add or edit `.md` files in the `docs` directory to write documentation content. Don't forget to organize each `.md` file into `index.md`.
  
   - **Build and preview documents locally**: the commands below will generate a `site` folder containing the generated static website. After that, you can preview the generated static website locally.
  
      ```bash
      mkdocs build # build static website
      mkdocs serve # preview static website
      ```

3. 𝗗𝗲𝗽𝗹𝗼𝘆 𝘁𝗵𝗲 `𝗠𝗸𝗗𝗼𝗰𝘀` 𝗽𝗿𝗼𝗷𝗲𝗰𝘁
   
   - **File hosting**: Push the document files to the project repository.
   
   - **Monitor document updates, automatically build and publish**
      1. you can achieve using the method in `Sphinx` above, i.e. through `Read the Docs`
      2. otherwise, you can use the CI/CD tool to automatically build and deploy the document. Here is an example of using `GitHub Actions` to make it. Note that this will push the generated static website to a new branch `gh-pages`.
         
         ```bash
         pip install ghp-import 

         mkdocs gh-deploy # deploy to GitHub Pages
         ```

</details>