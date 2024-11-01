# libgen-scraper

python script to search and donwload libgen.li files

inspired by libg.sh 

## Installation

cloning the repository.

## Usage

```bash
usage: libg.py [-h] [-b {author,title,publisher,year,isbn,language,md5,tags,extension}]
               [-n CANTIDAD_RESULTADOS]
               [-s {id,author,title,publisher,year,pages,language,filesize,extension}] [-r]
               [-p PROFUNDIDAD]
               ...

Descargar Libros de la pagina de genesis library, usando una query y opciones de busqueda.

positional arguments:
  query                 Terminos de busqueda para iniciar.

options:
  -h, --help            show this help message and exit
  -b {author,title,publisher,year,isbn,language,md5,tags,extension}, --buscar {author,title,publisher,year,isbn,language,md5,tags,extension}
                        La query se interpreta como el vslor de este argumento. Categorias
                        validas son: author, title, publisher, year, isbn, language, md5,
                        tags, extension. por defecto es titulo (title)
  -n CANTIDAD_RESULTADOS, --numero CANTIDAD_RESULTADOS
                        Numero de resultados maximo por pagina. Por defecto 100.
  -s {id,author,title,publisher,year,pages,language,filesize,extension}, --sortear {id,author,title,publisher,year,pages,language,filesize,extension}
                        Ordenar resultados por la categoria dada. Categorias validas son:id,
                        author, title, publisher, year, pages, language, filesize, extension.
                        Por defecto titulo (title).
  -r, --invertir        Invertir orden de resultados, orden descendiente.
  -p PROFUNDIDAD, -d PROFUNDIDAD, --profundidad PROFUNDIDAD
                        Cantidad de paginas resultado a recorrer. por defecto 10.
```

## Contributing

Not acepting contributors currently

## License


