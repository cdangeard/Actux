#Sys.setlocale('LC_ALL','French')
library(plotly)
library(aws.s3)
library(shiny)
library(shinydashboard)
library(shinycssloaders)
library(dplyr)
library(ggplot2)
Sys.setenv(AWS_DEFAULT_REGION = 'eu-west-3')

readFreadUt <- function(x){
  return(data.table::fread(x,encoding = 'UTF-8'))
}

dfArticles <- aws.s3::s3read_using(readFreadUt,
                                      object = "s3://actux-bucket/data_Actux.csv")


df <- aws.s3::s3read_using(readFreadUt,
                          object = "s3://actux-bucket/data_Actux_count.csv")


dfArticles$date_scrap <- as.Date(strptime(dfArticles$date_scrap,'%d/%m/%Y'))
dfArticles$date <- as.Date(strptime(dfArticles$date,'%d/%m/%Y'))
#df$date_scrap <- as.Date(strptime(df$date_scrap,'%d/%m/%Y'))
df$date <- as.Date(strptime(df$date,'%d/%m/%Y'))


# Define UI for application that draws a histogram
ui = dashboardPage(
  header = dashboardHeader(title = 'Actux'),
  sidebar = dashboardSidebar(
    sidebarMenu(id='menu',
                menuItem("Présentation",tabName = "pres", icon = icon("book")),
                menuItem("Données",tabName = "data", icon = icon("th")),
                menuItem("Recherche",tabName = "word",icon = icon("search"))
    ),
    conditionalPanel("input.menu == 'word'",
                textInput(inputId = 'searchWord', label = 'Recherche: ', value = "Bonjour"),
                dateInput('dateBegin',label= 'A partir du:',format = "yyyy-mm-dd",value= as.Date('2021-06-21')),
                dateInput('dateEnd',label= "jusqu'a:",format = "yyyy-mm-dd",value= Sys.Date())
    ),
    sidebarMenu(id='menu2',
                menuItem("Tendances",tabName = "trend",icon = icon("chart-line"))
    )
  ),
  body = dashboardBody(
    tabItems(
      tabItem(
        tabName = 'pres',
        h1('Bienvenue sur Actux'),
        p('Cette application utilise une base de données qui se met à jour tout les matins en scrappant les sites webs de certains grands quotidiens français.'),
        p("Les articles sont ensuite découpés par mots et lemmatisé, remplacement du mot par son lemme (infinitif, masculin singulier)."),
        p("voila."),
        p('ah oui mon github ', a(href = 'https://github.com/cdangeard', 'https://github.com/cdangeard', .noWS = "outside"), '!', .noWS = c("after-begin", "before-end")) 
      ),
      tabItem(
        tabName = "data",
        fluidRow(
          plotlyOutput("QteArticlesJourPlot")),
        fluidRow(
          box(
            title = "Date du dernier scrap :",
            background = "green",
            width = 4,
            textOutput("lastScrap")
          ),
          box(
            title = "Nombres d'articles :",
            background = "green",
            width = 4,
            textOutput("qteArticles")
          ),
          box(
            title = "Unique Lem :",
            background = "green",
            width = 4,
            textOutput("uniqueLem")
          )
        )
      ),
        tabItem(
          tabName = "word",
          fluidRow(
            column(width = 6,
                   plotlyOutput('barSearchJournalPlot')
                  ),
            column(width = 6,
                   plotlyOutput('lineSearchTimePlot')
                   )),br(),
          fluidRow(
            column(width = 9,
                   plotlyOutput('barSearchTimePlot')
                   ),
            column(width = 3,
                   box(
                     title = "Nombres d'articles :",
                     background = "green",
                     width = 12,
                     textOutput("nombreApparition")
                   ),box(
                     title = "Proportion d'articles :",
                     background = "green",
                     width = 12,
                     textOutput("propApparition")
                   ),box(
                     title = "Dernier article le :",
                     background = "green",
                     width = 12,
                     textOutput("lastApparition")
                   ),box(
                     title = "Jour du maximum d'articles :",
                     background = "green",
                     width = 12,
                     textOutput("bestApparition")
                   )
                )
               )
      ),
        tabItem(
          tabName = "trend",
          fluidRow(
            h1('Not done yet')
          )
      )
    )
  )
)

# Define server logic required to draw a histogram
server <- function(input, output) {

  ## Stats globales des articles scrappés
  output$QteArticlesJourPlot <- renderPlotly(
    dfArticles %>%
    filter(date >= '2021-06-21') %>%
    group_by(date, journal) %>%
    summarise(s = n()) %>%
    plot_ly(x = ~date, y = ~s, color = ~journal) %>%
    add_bars(hovertemplate = '%{y} articles le %{x}') %>%
    layout(barmode = 'stack',
           xaxis = list(title = 'Date'),
           yaxis = list(title = ''))%>%
      config(modeBarButtonsToRemove = c("zoomIn2d", "zoomOut2d", 'pan2d', 'autoScale2d', 'lasso2d', 'box2d'),
             displaylogo = FALSE)
  )
  
  output$qteArticles <- renderText(nrow(dfArticles))
  output$uniqueLem <- renderText(length(unique(df$listWords)))
  output$lastScrap <- renderText(format(max(dfArticles$date_scrap),'%d %b %Y'))
  
  ## Recherche
  output$nombreApparition <- renderText({
    validate(
      need(tolower(input$searchWord) %in% df$listWords & input$searchWord != '', "")
    )
    df %>%
      filter(date >= input$dateBegin & date <= input$dateEnd) %>%
      filter(listWords == tolower(input$searchWord)) %>% nrow()
  })
  
  output$propApparition <- renderText({
    validate(
      need(tolower(input$searchWord) %in% df$listWords & input$searchWord != '', "")
    )
    a <- df %>%
      filter(date >= input$dateBegin & date <= input$dateEnd) %>%
      filter(listWords == tolower(input$searchWord)) %>% nrow()
    b <- nrow(dfArticles)
    paste0(round(a*100/b, 2), '% des Articles')
    
  })
  
  output$lastApparition <- renderText({
    validate(
      need(tolower(input$searchWord) %in% df$listWords & input$searchWord != '', "")
    )
    df %>%
      filter(date >= input$dateBegin & date <= input$dateEnd) %>%
      filter(listWords == tolower(input$searchWord)) %>%
      pull(date) %>% max(na.rm = T) %>% format('%d %b %Y')
  })
  
  output$bestApparition <- renderText({
    validate(
      need(tolower(input$searchWord) %in% df$listWords & input$searchWord != '', "")
    )
    df %>% filter(listWords == tolower('bonjour')) %>%
      filter(date >= input$dateBegin & date <= input$dateEnd) %>%
      group_by(date) %>%
      summarise(countDay = sum(count,na.rm = T)) %>%
      filter(countDay == max(countDay)) %>% first() %>% 
      format('%d %b %Y')
  })
  
  
  output$barSearchJournalPlot <- renderPlotly({
    validate(
      need(tolower(input$searchWord) %in% df$listWords, "Lemme non présent dans les données")
    )
    validate(
      need(input$searchWord != '', "Entrez un lemme dans la barre de recherche")
    )
    df %>%
      filter(date >= input$dateBegin & date <= input$dateEnd) %>%
      filter(listWords == tolower(input$searchWord)) %>%
      group_by(journal) %>% 
      summarise(nombresMots = sum(count)) %>%
      plot_ly(x = ~journal, y = ~nombresMots) %>%
      add_bars(hovertemplate = '%{y} articles dans %{x}<extra></extra>') %>%
      layout(barmode = 'stack',
             yaxis = list(title = paste0("Nombre d'articles contenant ", input$searchWord)),
             xaxis = list(title = ''))%>%
      config(modeBarButtonsToRemove = c("zoomIn2d", "zoomOut2d", 'pan2d', 'autoScale2d', 'lasso2d', 'box2d'),
             displaylogo = FALSE)
  }
  )
  
  output$barSearchTimePlot <- renderPlotly({
    validate(
      need(tolower(input$searchWord) %in% df$listWords & input$searchWord != '', "")
    )
  df %>%
    filter(date >= input$dateBegin & date <= input$dateEnd) %>%
    filter(listWords == tolower(input$searchWord)) %>%
    group_by(date, journal) %>%
    summarise(s = sum(count)) %>%
    plot_ly(x = ~date, y = ~s, color = ~journal) %>%
    add_bars(hovertemplate = '%{y} articles le %{x}') %>%
    layout(barmode = 'stack',
           yaxis = list(title = paste0("Nombre d'articles contenant ", input$searchWord)),
           xaxis = list(title = 'Date'))%>%
    config(modeBarButtonsToRemove = c("zoomIn2d", "zoomOut2d", 'pan2d', 'autoScale2d', 'lasso2d', 'box2d'),
           displaylogo = FALSE)
  }
  )
  
  output$lineSearchTimePlot <- renderPlotly({
    validate(
      need(tolower(input$searchWord) %in% df$listWords & input$searchWord != '', "")
    )
    
    df %>%
      filter(date >= input$dateBegin & date <= input$dateEnd) %>%
      filter(listWords == tolower(input$searchWord)) %>%
      group_by(date) %>%
      summarise(s = sum(count)) %>%
      full_join(data.frame(date = seq(as.Date(min(.$date,na.rm = T)),
                                      as.Date(max(.$date,na.rm = T)),
                                      'days'), s = 0, by = c('date' = 'date'))) %>% 
      group_by(date) %>%
      summarise(s = sum(s)) %>%
      left_join(dfArticles %>% 
                  filter(date >= input$dateBegin & date <= input$dateEnd) %>% 
                  group_by(date) %>%
                  summarise(tot = n()), by = c('date' = 'date')) %>%
      mutate(prop = if_else(is.na(s/tot), 0, s/tot)) %>%
      plot_ly(x = ~date, y = ~prop) %>%
      add_lines() %>%
      layout(yaxis = list(title = paste0("Proportion d'articles contenant ", input$searchWord),
                          tickformat = '%'),
             xaxis = list(title = 'Date'))%>%
      config(modeBarButtonsToRemove = c("zoomIn2d", "zoomOut2d", 'pan2d', 'autoScale2d', 'lasso2d', 'box2d'),
             displaylogo = FALSE)
  }
  )
}

# Run the application 
shinyApp(ui = ui, server = server)

